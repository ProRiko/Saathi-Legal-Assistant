<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Foundation\Support\Providers\RouteServiceProvider as ServiceProvider;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;

class RouteServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        RateLimiter::for('chat', function (Request $request) {
            $perMinute = (int) config('rate_limiter.chat_per_minute', 30);
            return [
                Limit::perMinute($perMinute)->by($request->user()?->id ?: $request->ip()),
            ];
        });

        RateLimiter::for('documents', function (Request $request) {
            $perMinute = (int) config('rate_limiter.documents_per_minute', 10);
            return [
                Limit::perMinute($perMinute)->by($request->user()?->id ?: $request->ip()),
            ];
        });
    }
}
