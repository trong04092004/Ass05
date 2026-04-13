Set-Location d:\Bookstore_System_Microservice

$maps = @{
    'fashion-service'    = @(
        'https://images.pexels.com/photos/769733/pexels-photo-769733.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5698851/pexels-photo-5698851.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/985635/pexels-photo-985635.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/428340/pexels-photo-428340.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1124465/pexels-photo-1124465.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/267301/pexels-photo-267301.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2081199/pexels-photo-2081199.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/45055/pexels-photo-45055.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/45982/pexels-photo-45982.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1082529/pexels-photo-1082529.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1122017/pexels-photo-1122017.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'grocery-service'    = @(
        'https://images.pexels.com/photos/1346347/pexels-photo-1346347.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/628776/pexels-photo-628776.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/33783/olive-oil-salad-dressing-cooking-33783.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/8105074/pexels-photo-8105074.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5946973/pexels-photo-5946973.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/894695/pexels-photo-894695.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1410235/pexels-photo-1410235.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/616405/pexels-photo-616405.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1633525/pexels-photo-1633525.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1058240/pexels-photo-1058240.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4518658/pexels-photo-4518658.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1295572/pexels-photo-1295572.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'furniture-service'  = @(
        'https://images.pexels.com/photos/1350789/pexels-photo-1350789.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1866149/pexels-photo-1866149.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/46274/pexels-photo-46274.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6585599/pexels-photo-6585599.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/374074/pexels-photo-374074.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/667838/pexels-photo-667838.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6207942/pexels-photo-6207942.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/112811/pexels-photo-112811.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/276583/pexels-photo-276583.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1918291/pexels-photo-1918291.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/8469/red-blue-yellow-green.jpg?auto=compress&cs=tinysrgb&w=1200'
    )
    'beauty-service'     = @(
        'https://images.pexels.com/photos/3373747/pexels-photo-3373747.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3762804/pexels-photo-3762804.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6621463/pexels-photo-6621463.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2533266/pexels-photo-2533266.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3617544/pexels-photo-3617544.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7290089/pexels-photo-7290089.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7755526/pexels-photo-7755526.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6621337/pexels-photo-6621337.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2253832/pexels-photo-2253832.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/965989/pexels-photo-965989.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1961795/pexels-photo-1961795.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2113855/pexels-photo-2113855.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'sports-service'     = @(
        'https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3076509/pexels-photo-3076509.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/416717/pexels-photo-416717.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3822906/pexels-photo-3822906.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1552242/pexels-photo-1552242.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/416778/pexels-photo-416778.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3735207/pexels-photo-3735207.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/274422/pexels-photo-274422.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/2202685/pexels-photo-2202685.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/669584/pexels-photo-669584.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7675406/pexels-photo-7675406.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/863988/pexels-photo-863988.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'pet-service'        = @(
        'https://images.pexels.com/photos/4587991/pexels-photo-4587991.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5731866/pexels-photo-5731866.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7210260/pexels-photo-7210260.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1906153/pexels-photo-1906153.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4588435/pexels-photo-4588435.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7210754/pexels-photo-7210754.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7516509/pexels-photo-7516509.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6568944/pexels-photo-6568944.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4588003/pexels-photo-4588003.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4074742/pexels-photo-4074742.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/7210266/pexels-photo-7210266.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'stationery-service' = @(
        'https://images.pexels.com/photos/590493/pexels-photo-590493.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/159751/book-address-book-learning-159751.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/261763/pexels-photo-261763.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4226876/pexels-photo-4226876.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4226256/pexels-photo-4226256.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4145190/pexels-photo-4145190.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/6238039/pexels-photo-6238039.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3694884/pexels-photo-3694884.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5412268/pexels-photo-5412268.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4792509/pexels-photo-4792509.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4498188/pexels-photo-4498188.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/273238/pexels-photo-273238.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
    'toy-service'        = @(
        'https://images.pexels.com/photos/3661394/pexels-photo-3661394.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3933025/pexels-photo-3933025.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4226799/pexels-photo-4226799.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4473621/pexels-photo-4473621.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5697256/pexels-photo-5697256.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4473611/pexels-photo-4473611.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5697258/pexels-photo-5697258.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4473625/pexels-photo-4473625.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/5697264/pexels-photo-5697264.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/4473631/pexels-photo-4473631.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/1770824/pexels-photo-1770824.jpeg?auto=compress&cs=tinysrgb&w=1200',
        'https://images.pexels.com/photos/3658959/pexels-photo-3658959.jpeg?auto=compress&cs=tinysrgb&w=1200'
    )
}

foreach ($svc in $maps.Keys) {
    $path = Join-Path $svc 'seed_data.py'
    $src = Get-Content -Raw $path
    $m = [regex]::Match($src, "RAW_DATA = r'''(.*?)'''", [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $m.Success) {
        Write-Output "skip $svc"
        continue
    }

    $items = $m.Groups[1].Value | ConvertFrom-Json
    if ($items.Count -ne $maps[$svc].Count) {
        throw "count mismatch in $svc"
    }

    for ($i = 0; $i -lt $items.Count; $i++) {
        $items[$i].image_url = $maps[$svc][$i]
    }

    $newJson = $items | ConvertTo-Json -Depth 6
    $newSrc = $src.Substring(0, $m.Groups[1].Index) + $newJson + $src.Substring($m.Groups[1].Index + $m.Groups[1].Length)
    Set-Content -Path $path -Value $newSrc -Encoding UTF8
    Write-Output "updated $svc"
}

Write-Output 'done'
