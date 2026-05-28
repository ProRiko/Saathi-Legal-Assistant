<?php

namespace App\Policies;

use App\Models\User;
use App\Models\Conversation;

class ConversationPolicy
{
    public function view(User $user, Conversation $conversation): bool
    {
        return $conversation->user_id === $user->id;
    }
}
