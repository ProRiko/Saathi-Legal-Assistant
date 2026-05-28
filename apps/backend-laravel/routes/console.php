<?php

use Illuminate\Support\Facades\Artisan;

Artisan::command('saathi:health', function () {
    $this->info('Saathi Laravel backend is alive.');
});
