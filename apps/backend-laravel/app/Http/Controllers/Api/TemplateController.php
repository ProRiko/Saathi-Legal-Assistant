<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\TemplateGenerateRequest;
use App\Models\Template;
use App\Services\Template\TemplateService;

class TemplateController extends Controller
{
    public function __construct(private readonly TemplateService $templateService)
    {
    }

    public function index()
    {
        $templates = Template::query()
            ->where('is_active', true)
            ->orderBy('category')
            ->orderBy('title')
            ->get(['id', 'slug', 'category', 'title', 'description', 'schema', 'version']);

        return response()->json(['data' => $templates]);
    }

    public function generate(TemplateGenerateRequest $request)
    {
        $result = $this->templateService->generate($request->user(), $request->validated());
        return response()->json($result, 201);
    }
}
