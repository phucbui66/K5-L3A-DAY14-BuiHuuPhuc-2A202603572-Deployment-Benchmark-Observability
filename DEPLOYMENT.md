# Deployment

Chưa triển khai cloud, chưa có URL public hoặc ảnh xác nhận. Để hoàn tất, triển khai thư mục 06-lab-complete lên Railway hoặc Render, cấp Redis và đặt REDIS_URL, AGENT_API_KEY, RATE_LIMIT_PER_MINUTE, DAILY_BUDGET_USD trong cấu hình dịch vụ. Không lưu giá trị secret vào repo.

Kiểm tra /health và /ready trả 200; POST /ask không có key trả 401 và có key đúng trả 200. Ghi URL và lưu ảnh theo CHECKPOINTS.md sau khi triển khai thật.
