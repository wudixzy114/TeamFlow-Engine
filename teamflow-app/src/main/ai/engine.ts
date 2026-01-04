import {
  Llama,
  LlamaModel,
  LlamaContext,
  LlamaContextSequence,
  LlamaChatSession,
  ChatSessionModelFunctions, LlamaEmbeddingContext, LlamaEmbedding
} from "node-llama-cpp";
import {getModelPath} from "./config";
import {toolRegistry} from "./tools";
import {EMBED_MODEL_FILENAME} from "./config";
import {toolRetriever} from "./retriever";
import fs from "fs-extra";

export class AiEngine {
  public isReady = false;
  private llamaModule: typeof import("node-llama-cpp") | null = null;
  private llama: Llama | null = null;

  private chatModel: LlamaModel | null = null;
  private chatContext: LlamaContext | null = null;
  private chatSequence: LlamaContextSequence | null = null;
  private session: LlamaChatSession | null = null;

  private embedModel: LlamaModel | null = null;
  private embedContext: LlamaEmbeddingContext | null = null;

  async initLlama() {
    if (this.llama) return;
    try {
      console.log("[AI Engine] Dynamically importing node-llama-cpp...");
      this.llamaModule = await import("node-llama-cpp");
      const {getLlama, LlamaLogLevel} = this.llamaModule;
      this.llama = await getLlama({
        gpu: "auto",
        logLevel: LlamaLogLevel.warn
      });
      console.log("[AI Engine] Llama runtime initialized.");
    } catch (e) {
      console.error("[AI Engine] Failed to init Llama:", e);
      throw e;
    }
  }

  async initEmbeddingModel() {
    await this.initLlama()
    const modelPath = getModelPath(EMBED_MODEL_FILENAME)
    if (!fs.existsSync(modelPath)) {
      console.warn("[AI Engine] Embedding model not found, skipping vector features.");
      return;
    }
    console.log("[AI Engine] Loading embedding model...");
    this.embedModel = await this.llama!.loadModel(
      {
        modelPath: modelPath,
        gpuLayers: 'auto'
      }
    );
    this.embedContext = await this.embedModel.createEmbeddingContext({
      contextSize: 512,
      batchSize: 512
    })
    console.log("[AI Engine] Embedding engine ready.");
  }

  async getEmbedding(text: string): Promise<LlamaEmbedding> {
    if (!this.embedContext) {
      throw new Error("No embedding capability available.");
    }
    return await this.embedContext.getEmbeddingFor(text);
  }

  async loadModel(modelFilename: string) {
    await this.initLlama();
    if (!this.llama || !this.llamaModule) throw new Error("Llama runtime failed to initialize");
    const {LlamaChatSession} = this.llamaModule;

    this.initEmbeddingModel().then(async () => {
      // 确保 Retriever 能获取到 LlamaEmbedding 类型的数据
      await toolRetriever.indexTools();
    }).catch(err => {
      console.error("Failed to init embedding:", err);
    });

    const modelPath = getModelPath(modelFilename);
    if (!fs.existsSync(modelPath)) {
      throw new Error(`Model file not found at: ${modelPath}`);
    }

    await this.disposeCurrentSession();

    console.log(`[AI Engine] Loading model from: ${modelPath}`);

    this.chatModel = await this.llama.loadModel({
      modelPath: modelPath,
      gpuLayers: "auto"
    });

    this.chatContext = await this.chatModel.createContext({
      contextSize: 8192,
    });

    this.chatSequence = this.chatContext.getSequence();

    this.session = new LlamaChatSession({
      contextSequence: this.chatSequence,
      autoDisposeSequence: true,
      systemPrompt: "You are a helpful assistant. You can use the provided functions to assist the user.",
    });

    this.isReady = true;
    console.log("[AI Engine] Session created.");
  }

  /**
   * 聊天接口
   */
  async chat(message: string, onToken: (chunk: string) => void): Promise<string> {
    if (!this.session) throw new Error("Chat session not initialized.");

    const currentFunctions = await this.getFunctionsForTurn(message);

    return await this.session.prompt(message, {
      functions: currentFunctions,

      onToken: (tokens) => {
        const text = this.chatModel!.detokenize(tokens);
        onToken(text);
      },
      temperature: 0.7,
      topP: 0.8,
      topK: 20,
      minP: 0,
      maxTokens: this.chatContext?.contextSize,
    });
  }

  async resetSession() {
    if (this.session) {
      this.session.setChatHistory([]);
    }
  }

  private async getFunctionsForTurn(query: string): Promise<ChatSessionModelFunctions> {
    if (!this.llamaModule) await this.initLlama();
    const {defineChatSessionFunction} = this.llamaModule!;
    const relevantTools = await toolRetriever.retrieve(query, 5, 0.25);
    const functions: any = {};
    for (const tool of relevantTools) {
      functions[tool.name] = defineChatSessionFunction({
        description: tool.description,
        params: {
          type: 'object',
          properties: tool.parameters.properties,
        },
        handler: async (args: any) => {
          console.log(`[AI Engine] ⚡️ AI triggering tool: ${tool.name}`, args);
          try {
            return await toolRegistry.executeTool(tool.name, args);
          } catch (error: any) {
            return {error: error.message};
          }
        }
      })
    }

    return functions as ChatSessionModelFunctions;
  }

  // /**
  //  * 将 ToolRegistry 转换为 node-llama-cpp 的 ChatSessionModelFunctions 格式
  //  * @deprecated
  //  */
  // private async createSessionFunctions(): Promise<ChatSessionModelFunctions> {
  //   if (!this.llamaModule) await this.initLlama();
  //   const {defineChatSessionFunction} = this.llamaModule!;
  //
  //   const functions: any = {};
  //   const tools = toolRegistry.getAllTools();
  //
  //   for (const tool of tools) {
  //     functions[tool.name] = defineChatSessionFunction({
  //       description: tool.description,
  //       params: {
  //         type: "object",
  //         properties: tool.parameters.properties,
  //       },
  //       handler: async (args: any) => {
  //         console.log(`[AI Engine] ⚡️ AI triggering tool: ${tool.name}`, args);
  //         try {
  //           return await toolRegistry.executeTool(tool.name, args);
  //         } catch (error: any) {
  //           console.error(`[AI Engine] Tool execution failed:`, error);
  //           return {error: error.message};
  //         }
  //       }
  //     });
  //   }
  //   return functions as ChatSessionModelFunctions;
  // }

  private async disposeCurrentSession() {
    this.isReady = false;
    this.session = null;
    if (this.chatSequence) {
      this.chatSequence.dispose();
      this.chatSequence = null;
    }
    if (this.chatContext) {
      await this.chatContext.dispose();
      this.chatContext = null;
    }
    if (this.chatModel) {
      await this.chatModel.dispose();
      this.chatModel = null;
    }
  }
}

export const aiEngine = new AiEngine();
