<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;

class UserController extends Controller
{
    public function me()
    {
        return response()->json(['user' => auth()->user()]);
    }
}
