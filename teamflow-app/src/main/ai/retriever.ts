import {toolRegistry} from './tools';
import {aiEngine} from './engine';
import {AiTool} from '../../types/ai';
import {LlamaEmbedding} from "node-llama-cpp";

interface ScoredTool {
  tool: AiTool;
  score: number;
}

interface ToolEmbedding {
  name: string;
  vector: LlamaEmbedding;
}

class ToolRetriever {
  private embeddings: ToolEmbedding[] = []
  private isIndexed = false;

  async indexTools() {
    console.log('[ToolRetriever] Indexing tools...');
    const tools = toolRegistry.getAllTools();
    this.embeddings = [];

    for (const tool of tools) {
      try {
        const textToIndex = `${tool.name}: ${tool.description}`;
        const embedding = await aiEngine.getEmbedding(textToIndex);

        this.embeddings.push({
          name: tool.name,
          vector: embedding
        });
      } catch (e) {
        console.error(`[ToolRetriever] Failed to embed tool ${tool.name}`, e);
      }
    }

    this.isIndexed = true;
    console.log(`[ToolRetriever] Indexed ${this.embeddings.length} tools.`);
  }

  async retrieve(query: string, topK: number = 5, threshold: number = 0.2): Promise<AiTool[]> {
    if (!this.isIndexed) {
      if (toolRegistry.getAllTools().length > 10) {
        console.warn('[ToolRetriever] Not indexed & too many tools. Returning empty.');
        return [];
      }
      return toolRegistry.getAllTools();
    }

    try {
      const queryEmbedding = await aiEngine.getEmbedding(query);
      const scoredTools: ScoredTool[] = this.embeddings.map(item => ({
        tool: toolRegistry.getTool(item.name)!,
        score: queryEmbedding.calculateCosineSimilarity(item.vector)
      }));

      const result = scoredTools
        .filter(item => item.score >= threshold)
        .sort((a, b) => b.score - a.score)
        .slice(0, topK)
        .map(item => item.tool);

      console.log(`[ToolRetriever] Query: "${query}" matched tools:`, result.map(t => t.name));
      return result;
    } catch (e) {
      console.error('[ToolRetriever] Error during retrieval', e);
      return []
    }
  }
}

export const toolRetriever = new ToolRetriever();

