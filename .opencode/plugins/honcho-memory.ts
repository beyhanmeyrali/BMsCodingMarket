import type { Plugin } from "@opencode-ai/plugin"
import * as path from "path"

const SCRIPTS_DIR = path.resolve(
  import.meta.dirname,
  "../../plugins/honcho-bridge/scripts"
)

const PYTHON = "python"

async function storeToHoncho(
  $: any,
  sessionId: string,
  summary: string
): Promise<void> {
  const script = path.join(SCRIPTS_DIR, "store_to_honcho.py")
  const escaped = summary.replace(/'/g, "'\\''")
  try {
    await $`${PYTHON} "${script}" --session-id "${sessionId}" --summary "${escaped}"`
  } catch (err) {
    console.error("[honcho-memory] Failed to store:", err)
  }
}

export const HonchoMemoryPlugin: Plugin = async ({ client, $ }) => {
  const storedSessions = new Set<string>()

  return {
    "experimental.session.compacting": async (input, output) => {
      const sessionId: string = (input as any).session?.id ?? "unknown"

      output.context.push(`
## Memory Storage
After generating the compaction summary, this session's content will be stored
to Honcho persistent memory so it can be recalled in future sessions.
`)

      storedSessions.add(`compact:${sessionId}`)

      const summary = output.prompt
        ? `[Compaction] ${output.prompt.slice(0, 2000)}`
        : `[Session compacted: ${sessionId}]`

      await storeToHoncho($, sessionId, summary)
    },

    "session.idle": async ({ event }: any) => {
      const sessionId: string = event?.properties?.id ?? "unknown"

      if (storedSessions.has(`compact:${sessionId}`)) {
        return
      }

      try {
        const messages = await client.session.messages({
          path: { id: sessionId },
        })

        const recent = (messages.data ?? []).slice(-6)

        const lines: string[] = []
        for (const m of recent) {
          for (const part of m.parts ?? []) {
            if ((part as any).type === "text" && (part as any).text?.trim()) {
              const role = m.info?.role === "assistant" ? "Agent" : "User"
              lines.push(`${role}: ${(part as any).text.trim().slice(0, 500)}`)
            }
          }
        }

        if (lines.length === 0) return

        const summary = `[Session ${sessionId}]\n${lines.join("\n")}`
        await storeToHoncho($, sessionId, summary)
        storedSessions.add(`idle:${sessionId}`)
      } catch (err) {
        console.error("[honcho-memory] session.idle error:", err)
      }
    },
  }
}
