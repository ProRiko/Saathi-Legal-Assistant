<?php

namespace App\Services\Chat;

use App\Models\User;
use App\Models\Message;
use App\Models\Conversation;
use App\Services\AI\AIClient;
use App\Services\Usage\UsageService;
use Illuminate\Support\Str;
use Illuminate\Support\Carbon;

class ChatService
{
    public function __construct(
        private readonly AIClient $aiClient,
        private readonly UsageService $usageService,
    ) {
    }

    public function handle(User $user, array $data): array
    {
        $conversation = $this->resolveConversation($user, $data['conversation_id'] ?? null, $data['language'] ?? 'english');

        Message::create([
            'id' => (string) Str::uuid(),
            'conversation_id' => $conversation->id,
            'user_id' => $user->id,
            'role' => 'user',
            'content' => $data['message'],
            'created_at' => Carbon::now(),
        ]);

        $history = Message::query()
            ->where('conversation_id', $conversation->id)
            ->where('user_id', $user->id)
            ->orderByDesc('created_at')
            ->limit(14)
            ->get(['role', 'content'])
            ->reverse()
            ->values()
            ->toArray();

        $aiPayload = [
            'request_id' => (string) Str::uuid(),
            'user_ref' => (string) $user->id,
            'conversation_ref' => (string) $conversation->id,
            'language' => $conversation->language,
            'messages' => $history,
            'options' => [
                'max_tokens' => 700,
                'temperature' => 0.4,
            ],
        ];

        $ai = $this->aiClient->chat($aiPayload);

        $assistantMessage = Message::create([
            'id' => (string) Str::uuid(),
            'conversation_id' => $conversation->id,
            'user_id' => $user->id,
            'role' => 'assistant',
            'content' => (string) ($ai['reply'] ?? ''),
            'intent' => $ai['intent'] ?? null,
            'metadata' => [
                'guardrails' => $ai['guardrails'] ?? [],
                'raw_metadata' => $ai['metadata'] ?? [],
            ],
            'model_provider' => $ai['provider'] ?? null,
            'model_name' => $ai['model'] ?? null,
            'created_at' => Carbon::now(),
        ]);

        $conversation->update(['last_message_at' => Carbon::now()]);
        $this->usageService->increment($user->id, 'chat');

        return [
            'conversation_id' => $conversation->id,
            'message_id' => $assistantMessage->id,
            'reply' => $assistantMessage->content,
            'intent' => $assistantMessage->intent,
            'guardrails' => $assistantMessage->metadata['guardrails'] ?? [],
        ];
    }

    private function resolveConversation(User $user, ?string $conversationId, string $language): Conversation
    {
        if ($conversationId) {
            return Conversation::query()
                ->where('id', $conversationId)
                ->where('user_id', $user->id)
                ->firstOrFail();
        }

        return Conversation::create([
            'id' => (string) Str::uuid(),
            'user_id' => $user->id,
            'title' => 'New conversation',
            'language' => $language,
            'status' => 'active',
            'last_message_at' => Carbon::now(),
        ]);
    }
}
