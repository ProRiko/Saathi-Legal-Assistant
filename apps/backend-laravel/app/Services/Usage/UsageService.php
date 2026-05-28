<?php

namespace App\Services\Usage;

use App\Models\User;
use App\Models\UsageCounter;
use Illuminate\Support\Carbon;

class UsageService
{
    private const LIMITS = [
        'free' => ['chat' => 15, 'documents' => 3, 'ai_reviews' => 1, 'manual_reviews' => 1],
        'pro' => ['chat' => 200, 'documents' => 12, 'ai_reviews' => 8, 'manual_reviews' => 4],
        'legal_desk' => ['chat' => null, 'documents' => null, 'ai_reviews' => null, 'manual_reviews' => null],
    ];

    public function increment(int $userId, string $metric, int $amount = 1): void
    {
        $dateKey = Carbon::today()->toDateString();

        $counter = UsageCounter::query()->firstOrCreate([
            'user_id' => $userId,
            'metric' => $metric,
            'date_key' => $dateKey,
        ], ['count' => 0]);

        $counter->increment('count', $amount);
    }

    public function snapshot(User $user): array
    {
        $dateKey = Carbon::today()->toDateString();
        $tier = $user->tier ?? 'free';
        $limits = self::LIMITS[$tier] ?? self::LIMITS['free'];

        $usage = [];
        foreach (array_keys($limits) as $metric) {
            $count = UsageCounter::query()
                ->where('user_id', $user->id)
                ->where('metric', $metric)
                ->where('date_key', $dateKey)
                ->value('count') ?? 0;

            $usage[$metric] = [
                'used' => $count,
                'limit' => $limits[$metric],
            ];
        }

        return [
            'tier' => $tier,
            'date_key' => $dateKey,
            'usage' => $usage,
        ];
    }
}
