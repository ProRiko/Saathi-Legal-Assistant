<?php

namespace App\Providers;

use App\Models\Conversation;
use App\Models\GeneratedDocument;
use App\Policies\ConversationPolicy;
use App\Policies\GeneratedDocumentPolicy;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    protected $policies = [
        Conversation::class => ConversationPolicy::class,
        GeneratedDocument::class => GeneratedDocumentPolicy::class,
    ];

    public function boot(): void
    {
        $this->registerPolicies();
    }
}
