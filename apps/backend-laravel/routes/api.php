<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\ChatController;
use App\Http\Controllers\Api\TemplateController;
use App\Http\Controllers\Api\UserController;
use App\Http\Controllers\Api\UsageController;

Route::prefix('auth')->group(function () {
    Route::post('/signup', [AuthController::class, 'signup']);
    Route::post('/login', [AuthController::class, 'login']);
});

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/auth/logout', [AuthController::class, 'logout']);

    Route::post('/chat', [ChatController::class, 'store'])->middleware('throttle:chat');
    Route::get('/history', [ChatController::class, 'history']);
    Route::get('/history/{conversation}', [ChatController::class, 'show']);

    Route::get('/templates', [TemplateController::class, 'index']);
    Route::post('/template/generate', [TemplateController::class, 'generate'])->middleware('throttle:documents');

    Route::get('/usage', [UsageController::class, 'index']);
    Route::get('/me', [UserController::class, 'me']);
});
