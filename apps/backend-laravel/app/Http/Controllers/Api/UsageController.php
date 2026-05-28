<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\Usage\UsageService;

class UsageController extends Controller
{
    public function __construct(private readonly UsageService $usageService)
    {
    }

    public function index()
    {
        return response()->json($this->usageService->snapshot(auth()->user()));
    }
}
