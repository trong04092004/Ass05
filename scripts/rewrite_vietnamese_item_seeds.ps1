Set-Location d:\Bookstore_System_Microservice

function Get-RawItemsFromSeed {
    param([string]$seedPath)
    $src = Get-Content -Raw -Path $seedPath
    $m = [regex]::Match($src, "RAW_DATA = r'''(.*?)'''", [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $m.Success) {
        throw "RAW_DATA not found in $seedPath"
    }
    return ($m.Groups[1].Value | ConvertFrom-Json)
}

function Get-CategoryImagesFromSeed {
    param([string]$seedPath)
    $src = Get-Content -Raw -Path $seedPath
    $matches = [regex]::Matches($src, "https://images\.pexels\.com/photos/[^'\"\s]+")
    $arr = @()
    foreach ($x in $matches) { $arr += $x.Value }
    $arr = $arr | Select-Object -Unique
    if ($arr.Count -eq 0) {
        throw "No pexels image URL found in $seedPath"
    }
    return $arr
}

function Rewrite-SeedFile {
    param(
        [string]$Service,
        [string]$SettingsModule,
        [string]$Label,
        [string[]]$VietnameseNames
    )

    $seedPath = Join-Path (Get-Location) "$Service\seed_data.py"
    $items = Get-RawItemsFromSeed -seedPath $seedPath
    $images = Get-CategoryImagesFromSeed -seedPath $seedPath

    if ($items.Count -ne $VietnameseNames.Count) {
        throw "Item count mismatch at $Service: expected $($items.Count), got $($VietnameseNames.Count)"
    }

    for ($i = 0; $i -lt $items.Count; $i++) {
        $items[$i].name = $VietnameseNames[$i]
        $items[$i].description = "$($VietnameseNames[$i]) là sản phẩm được tuyển chọn kỹ, chú trọng chất lượng, độ bền và trải nghiệm sử dụng thực tế."
        $items[$i] | Add-Member -NotePropertyName image_url -NotePropertyValue $images[$i % $images.Count] -Force
    }

    $json = $items | ConvertTo-Json -Depth 5

    $content = @"
        import os
        import json
        import django
        from decimal import Decimal

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$SettingsModule')
        django.setup()

        from app.models import Product

        RAW_DATA = r'''$json'''
        samples = json.loads(RAW_DATA)

        deleted_count, _ = Product.objects.all().delete()
        print(f'Deleted old products: {deleted_count}')

        for item in samples:
        payload = {
            'name': item['name'],
            'sku': item['sku'],
            'brand': item['brand'],
            'price': Decimal(str(item['price'])),
            'stock_quantity': int(item['stock_quantity']),
            'description': item['description'],
            'image_url': item['image_url'],
        }
        Product.objects.update_or_create(sku=payload['sku'], defaults=payload)

        print('Seeded $Label with Vietnamese item-level products and images')
        "@

    Set-Content -Path $seedPath -Value $content -Encoding UTF8
}

$maps = @{
    'electronics-service' = @('Laptop Asus VivoBook 15 OLED','Laptop Dell Inspiron 14 Plus','Tai nghe Apple AirPods Pro 2','Tai nghe Sony WH-1000XM5','Máy tính bảng Samsung Galaxy Tab S9 FE','Sạc nhanh GaN Xiaomi 67W','Pin sạc dự phòng Anker 737 24.000mAh','Chuột không dây Logitech MX Master 3S','Bàn phím cơ Keychron K8 Pro','Màn hình LG UltraWide 29WP500','Bộ định tuyến TP-Link Archer AX55','Ổ cứng di động WD My Passport 2TB')
    'fashion-service' = @('Áo sơ mi linen nam','Quần tây slimfit công sở','Váy midi họa tiết nhẹ','Áo thun basic cotton','Áo khoác denim cổ điển','Giày sneaker năng động','Giày loafer da tối giản','Túi tote canvas hằng ngày','Thắt lưng da cao cấp','Áo len cardigan oversize','Quần jeans dáng momfit','Mũ lưỡi trai phong cách đường phố')
    'grocery-service' = @('Gạo ST25 thượng hạng 5kg','Mì spaghetti Ý 500g','Dầu ô liu extra virgin 1L','Yến mạch nguyên cám 1kg','Sữa tươi không đường 1L','Cà phê hạt rang mộc 500g','Đường nâu organic 1kg','Muối hồng Himalaya 500g','Bơ đậu phộng crunchy 340g','Mật ong nguyên chất 700ml','Nước tương ít natri 500ml','Hạt điều rang muối 250g')
    'furniture-service' = @('Bàn ăn gỗ sồi 4 ghế','Sofa vải nỉ 3 chỗ','Kệ sách đứng 5 tầng','Giường ngủ gỗ 1m6','Tủ quần áo 3 cánh','Bàn làm việc chân sắt','Ghế công thái học văn phòng','Bàn trà phòng khách','Đèn cây trang trí phòng ngủ','Tủ đầu giường tối giản','Gương đứng toàn thân','Thảm lót sàn phong cách Bắc Âu')
    'beauty-service' = @('Sữa rửa mặt dịu nhẹ 150ml','Nước cân bằng da 200ml','Tinh chất vitamin C 30ml','Kem dưỡng ẩm phục hồi 50ml','Kem chống nắng SPF50+ 50ml','Mặt nạ đất sét 100g','Tẩy tế bào chết dịu nhẹ 120ml','Nước tẩy trang micellar 400ml','Son dưỡng môi thiên nhiên','Xịt khoáng làm dịu 150ml','Nước hoa nữ floral 50ml','Kem nền mỏng nhẹ 30ml')
    'sports-service' = @('Giày chạy bộ nam thoáng khí','Áo thể thao nữ thấm hút mồ hôi','Quần short tập luyện co giãn','Thảm yoga chống trượt 6mm','Tạ tay bọc cao su 5kg','Dây kháng lực đa mức','Bình nước thể thao 1 lít','Bóng đá tiêu chuẩn số 5','Vợt cầu lông carbon nhẹ','Băng bảo vệ đầu gối thể thao','Găng tay tập gym chống trượt','Túi thể thao đa năng 35L')
    'pet-service' = @('Hạt khô cho chó trưởng thành 3kg','Hạt khô cho mèo vị cá hồi 2kg','Pate mèo cao cấp 85g','Cát vệ sinh mèo khử mùi 10L','Sữa tắm chó mèo dịu nhẹ 500ml','Vòng cổ da cho chó','Dây dắt chó phản quang','Nhà nệm cho mèo','Đồ chơi gặm nhai cho chó','Bát ăn inox chống trượt','Xịt khử mùi chuồng nuôi 300ml','Vitamin tổng hợp cho thú cưng')
    'stationery-service' = @('Sổ tay bìa cứng A5','Bút bi mực xanh 0.5mm','Bút chì gỗ HB hộp 12 cây','Tẩy trắng ít bụi','Thước kẻ nhựa 30cm','Bút highlight 5 màu','Giấy ghi chú sticky note','Bấm kim số 10','Kẹp giấy màu hộp 100 cái','Bìa hồ sơ nhựa A4','Keo dán khô 21g','Kéo học sinh lưỡi an toàn')
    'toy-service' = @('Bộ xếp hình thành phố 500 mảnh','Gấu bông mềm cao cấp','Xe điều khiển địa hình','Búp bê thời trang cho bé gái','Bộ đồ chơi nấu ăn mini','Bảng vẽ từ tính đa năng','Bóng ném mềm cho trẻ em','Bộ lego robot sáng tạo','Đàn piano đồ chơi điện tử','Bộ tàu hỏa đường ray','Bộ thẻ học chữ cái tiếng Việt','Bộ đất nặn an toàn 24 màu')
}

$settings = @{
    'electronics-service'='electronics_service.settings';
    'fashion-service'='fashion_service.settings';
    'grocery-service'='grocery_service.settings';
    'furniture-service'='furniture_service.settings';
    'beauty-service'='beauty_service.settings';
    'sports-service'='sports_service.settings';
    'pet-service'='pet_service.settings';
    'stationery-service'='stationery_service.settings';
    'toy-service'='toy_service.settings';
}

foreach ($svc in $maps.Keys) {
    Rewrite-SeedFile -Service $svc -SettingsModule $settings[$svc] -Label $svc -VietnameseNames $maps[$svc]
}

Write-Output "Rewrite completed for all category services."
