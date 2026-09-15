param(
    [string]$Root = (Split-Path $PSScriptRoot -Parent),
    [string[]]$Sources = @('examples/standard.docx', 'examples/technical-blog.docx', 'examples/style-coverage.docx'),
    [string]$OutputDirectory = 'previews',
    [switch]$CheckAlignment
)

# Optional visual validation with locally installed Microsoft Word.
# Documents are opened read-only, without adding them to Recent Documents.
$ErrorActionPreference = 'Stop'
$word = $null
$document = $null
$results = @()
$outputPath = Join-Path $Root $OutputDirectory
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
$staging = Join-Path ([IO.Path]::GetTempPath()) ('typora-word-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null

try {
    Write-Output 'Starting Microsoft Word...'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    foreach ($source in $Sources) {
        $inputPath = Join-Path $Root $source
        $pdfPath = Join-Path $outputPath (([IO.Path]::GetFileNameWithoutExtension($source)) + '.pdf')
        # Stage locally: Office can stall when opening a WSL network-share path.
        $localInput = Join-Path $staging ([IO.Path]::GetFileName($source))
        $localPdf = [IO.Path]::ChangeExtension($localInput, '.pdf')
        Copy-Item -LiteralPath $inputPath -Destination $localInput
        Write-Output ('Opening ' + $source)
        $document = $word.Documents.Open($localInput, $false, $true, $false)
        $document.Fields.Update() | Out-Null
        foreach ($toc in $document.TablesOfContents) { $toc.Update() }
        $document.Repaginate()
        if ($CheckAlignment) {
            foreach ($table in $document.Tables) {
                if ($table.Rows.Alignment -ne 1) { throw ('Table is not centered: ' + $source) }
            }
            foreach ($paragraph in $document.Paragraphs) {
                $styleName = $paragraph.Range.Style.NameLocal
                if ($styleName -in @('Figure', 'Captioned Figure', 'Image Caption', 'Table Caption')) {
                    if ($paragraph.Alignment -ne 1) { throw ('Figure/caption is not centered: ' + $source + ' / ' + $styleName) }
                }
            }
            Write-Output ('PASS Word table and figure alignment: ' + $source)
        }
        $pages = $document.ComputeStatistics(2)
        Write-Output ('Exporting ' + $pages + ' pages...')
        $document.ExportAsFixedFormat($localPdf, 17)
        Copy-Item -LiteralPath $localPdf -Destination $pdfPath -Force
        $results += [PSCustomObject]@{
            source = $source
            pdf = $pdfPath
            pages = $pages
            wordVersion = $word.Version
            wordBuild = $word.Build
        }
        $document.Close(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null
        $document = $null
    }
    $results | ConvertTo-Json
} finally {
    if ($null -ne $document) {
        $document.Close(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null
    }
    if ($null -ne $word) {
        $word.Quit()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null
    }
    Remove-Item -LiteralPath $staging -Recurse -Force
}
