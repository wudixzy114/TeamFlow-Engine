import {AI_IPC_CHANNELS, AiTool} from "../../types/ai";
import {BrowserWindow} from "electron";

const THEME_OPTIONS = ['focus', 'connection', 'zen', 'clean', 'synthwave', 'abyss'];

class ToolRegistry {
  private tools: Map<string, AiTool> = new Map()

  constructor() {
    this.registerBuiltInTools()
    this.registerTimerTools()
    this.registerCheckinTools()
    this.registerThemeTools()
    this.registerSocialTools()
  }

  getTool(name: string): AiTool | undefined {
    return this.tools.get(name)
  }

  registerTool(tool: AiTool) {
    if (this.tools.has(tool.name)) {
      console.warn(`[AI Tool] Tool '${tool.name}' is being overwritten.`);
    }
    this.tools.set(tool.name, tool);
    console.log(`[AI Tool] Registered: ${tool.name}`);
  }

  getDefinitions() {
    return Array.from(this.tools.values()).map((t) => ({
      type: 'function',
      function: {
        name: t.name,
        description: t.description,
        parameters: t.parameters,
      },
    }));
  }

  async executeTool(name: string, args: any): Promise<any> {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new Error(`Tool '${name}' not found.`);
    }

    try {
      console.log(`[AI Tool] Executing ${name} with args:`, args);
      const result = await tool.handler(args);
      console.log(`[AI Tool] Result for ${name}:`, result);
      return result;
    } catch (error: any) {
      console.error(`[AI Tool] Execution failed:`, error);
      return {error: error.message || 'Unknown tool execution error'};
    }
  }

  getAllTools(): AiTool[] {
    return Array.from(this.tools.values());
  }

  private registerThemeTools() {
    this.registerTool({
      name: 'ui_set_theme',
      description: 'Set the application visual theme. Use "focus" or "zen" for deep work, "connection" for social, "clean" for light mode.',
      parameters: {
        type: 'object',
        properties: {
          theme: {
            type: 'string',
            enum: THEME_OPTIONS,
            description: 'The theme name to apply.'
          }
        },
      },
      scope: 'renderer',
      handler: async (args) => this.dispatchToRenderer('ui:set-theme', args)
    });

    this.registerTool({
      name: 'ui_cycle_theme',
      description: 'Switch to the next available theme randomly or sequentially.',
      parameters: {type: 'object', properties: {}},
      scope: 'renderer',
      handler: async (args) => this.dispatchToRenderer('ui:cycle-theme', args)
    });
  }

  private registerSocialTools() {
    this.registerTool({
      name: 'social_post_highlight',
      description: 'Post a new highlight (moment of recognition or achievement) to the team feed.',
      parameters: {
        type: 'object',
        properties: {
          content: {
            type: 'string',
            description: 'The content of the highlight post.'
          }
        },
      },
      scope: 'renderer',
      handler: async (args) => this.dispatchToRenderer('social:post-highlight', args)
    });
  }

  private registerCheckinTools() {
    this.registerTool({
      name: 'flow_submit_checkin',
      description: 'Submit a daily flow check-in. Infer the challenge and skill levels (-1.0 to 1.0) based on the user\'s feeling. ' +
        'Rules: Anxiety(High Challenge, Low Skill), Flow(High Challenge, High Skill), Boredom(Low Challenge, High Skill), Apathy(Low Challenge, Low Skill).',
      parameters: {
        type: 'object',
        properties: {
          challenge_level: {
            type: 'number',
            description: 'Level of challenge perceived (-1.0 to 1.0).'
          },
          skill_level: {
            type: 'number',
            description: 'Level of skill perceived (-1.0 to 1.0).'
          },
          achievement_text: {
            type: 'string',
            description: 'What was achieved today (optional).'
          },
          obstacle_text: {
            type: 'string',
            description: 'What obstacles were faced (optional).'
          }
        },
      },
      scope: 'renderer',
      handler: async (args) => this.dispatchToRenderer('flow:submit-checkin', args)
    });
  }

  private registerTimerTools() {
    this.registerTool({
      name: 'timer_manage_session',
      description: 'Add a new timer block to the schedule. Can be a focus task or a break. If duration is omitted, default settings are used.',
      parameters: {
        type: 'object',
        properties: {
          type: {
            type: 'string',
            enum: ['focus', 'short_break', 'long_break'],
            description: 'The type of the session.'
          },
          task_description: {
            type: 'string',
            description: 'Description of the task (only for focus type). Default: "Deep Work"'
          },
          duration: {
            type: 'number',
            description: 'Duration in minutes. Optional (uses user settings if null).'
          },
          start_immediately: {
            type: 'boolean',
            description: 'Whether to start this session immediately. Default: true.'
          }
        },
      },
      scope: 'renderer',
      handler: async (args) => {
        return this.dispatchToRenderer('timer:manage-session', args);
      }
    });
    this.registerTool({
      name: 'timer_control',
      description: 'Pause or resume the current timer.',
      parameters: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            enum: ['pause', 'resume'],
            description: 'The action to perform.'
          }
        },
      },
      scope: 'renderer',
      handler: async (args) => {
        return this.dispatchToRenderer('timer:control', args);
      }
    });
    this.registerTool({
      name: 'timer_modify_active',
      description: 'Modify the currently active timer block. Can rename task, extend time, shorten time, or set absolute duration.',
      parameters: {
        type: 'object',
        properties: {
          new_description: {
            type: 'string',
            description: 'New task description (renames the current task).'
          },
          time_adjustment: {
            type: 'number',
            description: 'Minutes to add (positive) or remove (negative).'
          },
          set_duration: {
            type: 'number',
            description: 'Set the remaining time to exactly this many minutes.'
          }
        }
      },
      scope: 'renderer',
      handler: async (args) => {
        return this.dispatchToRenderer('timer:modify-active', args);
      }
    });
    this.registerTool({
      name: 'timer_skip_current',
      description: 'Skip the current active task/timer and switch to the next one in the schedule.',
      parameters: {
        type: 'object',
        properties: {},
      },
      scope: 'renderer',
      handler: async (args) => {
        return this.dispatchToRenderer('timer:skip', args);
      }
    });
  }

  private async dispatchToRenderer(action: string, args: any) {
    const wins = BrowserWindow.getAllWindows();
    const win = wins[0]; // 简单起见，取第一个窗口
    if (!win || win.isDestroyed()) {
      throw new Error("Application window not found.");
    }
    win.webContents.send(AI_IPC_CHANNELS.EXECUTE_RENDERER_ACTION, {
      action,
      args
    });
    return {status: 'command_sent_to_ui', action, params: args};
  }

  private registerBuiltInTools() {
    this.registerTool({
      name: 'get_current_time',
      description: 'Get the current system time and date.',
      parameters: {
        type: 'object',
        properties: {}, // 无需参数
      },
      scope: 'main',
      handler: async () => {
        return new Date().toLocaleString();
      },
    });
  }
}

export const toolRegistry = new ToolRegistry();
