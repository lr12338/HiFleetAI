export type TestChatRequest = {
  conversation_id: string | null;
  message: string;
  display_name?: string;
};

export type TestChatToolCall = {
  tool_name: string;
  status: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown> | null;
};

export type TestChatSource = {
  source_type: string;
  title: string;
  snippet: string;
};

export type TestChatResponse = {
  conversation_id: string;
  message_id: string;
  handoff_status: string;
  reply: {
    type: string;
    content: string;
  };
  tool_calls: TestChatToolCall[];
  sources: TestChatSource[];
  metadata: Record<string, unknown>;
};

type ApiErrorPayload = {
  detail?: string;
};

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (typeof payload.detail === 'string' && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parsing failures and fall through to a generic message.
  }

  return `Request failed with status ${response.status}`;
}

export async function createTestChatCompletion(
  payload: TestChatRequest,
): Promise<TestChatResponse> {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      conversation_id: payload.conversation_id,
      channel_type: 'console',
      user: {
        user_id: null,
        display_name: payload.display_name ?? 'Console Test User',
      },
      message: {
        type: 'text',
        content: payload.message,
        attachments: [],
      },
      metadata: {
        source: 'console_test_chat',
      },
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as TestChatResponse;
}
