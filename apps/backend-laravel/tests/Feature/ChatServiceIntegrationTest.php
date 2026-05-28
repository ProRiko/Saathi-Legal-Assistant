<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use App\Services\Chat\ChatService;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Hash;
use Illuminate\Foundation\Testing\RefreshDatabase;

class ChatServiceIntegrationTest extends TestCase
{
    use RefreshDatabase;

    public function test_chat_service_persists_messages_and_calls_ai_with_signature(): void
    {
        config()->set('ai.base_url', 'http://python-ai.internal');
        config()->set('ai.internal_key', 'test-key');
        config()->set('ai.internal_secret', 'test-secret');

        Http::fake(function ($request) {
            $this->assertEquals('test-key', $request->header('X-Internal-Key')[0] ?? null);
            $this->assertNotEmpty($request->header('X-Request-Timestamp')[0] ?? null);
            $this->assertNotEmpty($request->header('X-Internal-Signature')[0] ?? null);

            $this->assertStringContainsString('/ai/chat', $request->url());

            return Http::response([
                'reply' => 'You can issue a legal notice for unpaid salary.',
                'intent' => 'employment_law',
                'provider' => 'claude',
                'model' => 'claude-3-5-haiku-20241022',
                'guardrails' => ['added_citation' => true],
                'metadata' => ['language' => 'english'],
            ], 200);
        });

        $user = User::query()->create([
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => Hash::make('password123'),
            'tier' => 'free',
            'status' => 'active',
        ]);

        $service = app(ChatService::class);

        $result = $service->handle($user, [
            'message' => 'My salary is not paid for 2 months',
            'language' => 'english',
        ]);

        $this->assertArrayHasKey('conversation_id', $result);
        $this->assertEquals('employment_law', $result['intent']);

        $this->assertDatabaseCount('conversations', 1);
        $this->assertDatabaseCount('messages', 2);
        $this->assertDatabaseHas('messages', [
            'user_id' => $user->id,
            'role' => 'assistant',
            'intent' => 'employment_law',
        ]);
    }
}
