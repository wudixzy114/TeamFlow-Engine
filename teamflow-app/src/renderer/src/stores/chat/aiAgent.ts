import {isSpecialTag, getTagConfig} from './chatTags';

class AiAgentService {
  private processedMessageIds = new Set<string>()

  public inspect(messages: TeamChat[]) {
    messages.forEach(msg => {
      if (this.processedMessageIds.has(msg.id)) return;
      this.processedMessageIds.add(msg.id);
      if (isSpecialTag(msg.tag)) {
        this.triggerCallback(msg)
      }
    })
  }

  public clearCache() {
    this.processedMessageIds.clear();
  }

  private triggerCallback(msg: TeamChat) {
    const config = getTagConfig(msg.tag);
    if (!config) return;
    console.log(`[AI Agent] Detected intent: ${config.label}, Content: ${msg.content}`);

    // 这里是实际调用 AI 接口的地方
  }
}

export const aiAgent = new AiAgentService()
