<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\ChatRequest;
use App\Models\Conversation;
use App\Services\Chat\ChatService;

class ChatController extends Controller
{
    public function __construct(private readonly ChatService $chatService)
    {
    }

    public function store(ChatRequest $request)
    {
        $result = $this->chatService->handle($request->user(), $request->validated());
        return response()->json($result);
    }

    public function history()
    {
        $items = Conversation::query()
            ->where('user_id', auth()->id())
            ->orderByDesc('last_message_at')
            ->paginate(30);

        return response()->json($items);
    }

    public function show(Conversation $conversation)
    {
        $this->authorize('view', $conversation);

        $conversation->load(['messages' => fn ($q) => $q->orderBy('created_at')]);
        return response()->json($conversation);
    }
}
