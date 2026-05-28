<?php

namespace App\Policies;

use App\Models\User;
use App\Models\GeneratedDocument;

class GeneratedDocumentPolicy
{
    public function view(User $user, GeneratedDocument $document): bool
    {
        return $document->user_id === $user->id;
    }
}
