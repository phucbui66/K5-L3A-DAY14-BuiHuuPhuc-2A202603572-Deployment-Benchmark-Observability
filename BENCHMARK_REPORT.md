# Benchmark & Observability Report — Day 14

**Họ tên:** Bùi Hữu Phúc

**Môi trường:** Windows, Python 3.11.9 nhúng tạm thời; agent develop chạy local.
**Điều kiện:** Mỗi phép load dùng 300 requests. MOCK_ERROR_RATE=0 để đo ổn định, khác giá trị mặc định 0.01. Load concurrency dùng MOCK_SLOW_RATE=0.03. Các file số liệu gốc nằm trong [reports/](reports/). Đây là một lần chạy trên máy local, không đại diện hiệu năng cloud.

## 1. SLO

| SLI | Mục tiêu sử dụng khi chạy |
|---|---|
| p95 latency | ≤ 500 ms |
| Error rate | ≤ 2% |
| Accuracy | ≥ 85% cho CI; phép kiểm cuối v2 yêu cầu 100% |

Ngưỡng latency và lỗi là mặc định của load test; accuracy 85% là yêu cầu quality gate trong bài.

## 2. Benchmark hiệu năng

### 2.1 Concurrency

| Concurrency | RPS | p50 ms | p95 ms | p99 ms | Error rate | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 4.15 | 203.0 | 234.4 | 1696.2 | 0% | Đạt |
| 10 | 38.77 | 188.3 | 232.6 | 1686.5 | 0% | Đạt |
| 50 | 104.83 | 200.4 | 265.1 | 1720.8 | 0% | Đạt |
| 100 | 47.55 | 702.0 | 4747.4 | 5139.3 | 0% | Không đạt p95 |

RPS không tăng tuyến tính: nó tăng đến 50 rồi giảm ở 100 trong lần đo này; có dấu hiệu nghẽn hoặc xếp hàng, nhưng cần đo CPU và kết nối để xác định nút thắt. Không suy ra capacity production từ một lần chạy.

### 2.2 Tail latency, concurrency 20

| MOCK_SLOW_RATE | avg ms | p95 ms | p99 ms |
|---:|---:|---:|---:|
| 0 | 191.4 | 221.7 | 230.5 |
| 0.03 | 213.5 | 219.4 | 1682.1 |
| 0.1 | 332.5 | 1696.2 | 1718.6 |

Khi một phần nhỏ request chậm, p99 phản ánh phần đuôi mà trung bình che đi. Khi tỷ lệ chậm tiến gần hoặc vượt 5%, p95 cũng tăng mạnh. Mẫu ngẫu nhiên khiến p95 của 0.03 không nhất thiết tăng so với 0.

## 3. Benchmark chất lượng

| Chỉ số | v1 | v2 trước sửa | v2 sau sửa |
|---|---:|---:|---:|
| Accuracy | 4.3% (1/23) | 91.3% (21/23) | 100% (23/23) |
| Avg tokens/câu | 57.5 | 108.8 | 112.1 |
| Tổng cost USD | 0.000409 | 0.000757 | 0.000777 |
| Cost/câu đúng USD | 0.00040935 | 0.00003607 | 0.00003378 |
| Quality gate | FAIL (80%) | PASS (80%) | PASS (100%, không regression) |

V2 trước sửa lấy từ bản gốc trong Git, chạy riêng với cùng dataset; v2 sau sửa dùng knowledge base trong repo. Tắt lỗi mock ngẫu nhiên; latency vẫn có jitter và slow rate mặc định. Kết quả trước sửa thiếu hai câu security-02 (JWT) và scaling-03 (HPA). Bổ sung tài liệu JWT và HPA vào knowledge base đã xử lý cả hai, không đổi golden dataset.

V2 tốn token/câu và tổng chi phí hơn v1 nhưng trả lời đúng nhiều hơn, nên cost/câu đúng thấp hơn trên mẫu này. So sánh chỉ áp dụng cho mock và dataset trong bài.

## 4. Observability stack

Đã chạy stack Docker Desktop; kiểm tra quy tắc Prometheus bằng promtool trả SUCCESS. Bằng chứng: [Grafana](screenshots/grafana-dashboard.png), [trace chậm](screenshots/jaeger-slow-trace.png), [trace lỗi](screenshots/jaeger-error-trace.png), [hai alert firing](screenshots/prometheus-alert-firing.png).

Trong lúc chạy tải, dashboard từng hiển thị p95 khoảng 498 ms, error rate 1,01%, traffic 59,4 request/s và một instance up. Đây là giá trị tức thời, không phải số tổng hợp từ CSV.

Thí nghiệm đồng thời đặt MOCK_ERROR_RATE=0.2 và MOCK_SLOW_RATE=0.3 lúc 21:35:35 UTC, tạo tải 100 users. Prometheus ghi activeAt lúc 21:35:57 UTC cho cả hai alert. Lần kiểm tra lúc 21:37:44 thấy AgentHighErrorRate đã firing và AgentHighLatencyP95 pending; lúc 21:38:01 cả hai firing. Như vậy alert lỗi được quan sát firing trong vòng 129 giây, alert latency trong vòng 146 giây sau khi đổi cấu hình; thời điểm firing chính xác nằm giữa các lần kiểm tra. Rule yêu cầu điều kiện duy trì lần lượt 1 và 2 phút.

Trace chậm `19b04944dad6000c008ddb0782788247` có HTTP request 1757,8 ms theo log; bước LLM 1655,0 ms (khoảng 94%). Trace lỗi `bc58d8c1c730affde832691b4f8ec7d3` trả HTTP 503 và span LLM có event exception. Dòng log tương ứng:

```json
{"ts":"2026-11-25T21:28:16.391611+00:00","event":"llm_call","trace_id":"19b04944dad6000c008ddb0782788247","request_id":"9a5eb2744def","model":"mock-llm-small","llm_ms":1655.0}
{"ts":"2026-11-25T21:26:45.553524+00:00","event":"llm_error","trace_id":"bc58d8c1c730affde832691b4f8ec7d3","request_id":"2c7c0c68c3ad","error":"Upstream LLM error: 503 Service Unavailable (mock)"}
```

Các dòng trên trích các trường chính từ log, không chứa toàn bộ field gốc.

Suy giảm chất lượng không nhất thiết làm latency hay error rate xấu đi; cần eval định kỳ trên golden dataset và so sánh baseline/quality gate, có thể bổ sung theo dõi phản hồi người dùng.

## 5. Benchmark scaling

Locust headless: 100 users, ramp 10/s, 2 phút. Bảng chỉ dùng dòng POST /ask; lỗi mock mặc định là 1%. Dữ liệu gốc tại [scale_1_stats.csv](benchmark-results/scale_1_stats.csv) và [scale_3_stats.csv](benchmark-results/scale_3_stats.csv).

| Instances | Requests | RPS | p50 ms | p95 ms | p99 ms | Failures |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7108 | 59,48 | 200 | 340 | 1700 | 64 |
| 3 | 7138 | 59,74 | 190 | 230 | 1700 | 83 |

Trong lần đo này p95 giảm từ 340 xuống 230 ms, còn RPS gần như không đổi. Đây là tải có thời gian chờ giữa các request; một lần đo chưa đủ để xác định nút thắt hay hiệu năng tối đa.

## 6. Nhận xét

- Theo dõi percentile bên cạnh trung bình để thấy tail latency.
- Đo accuracy, token và chi phí cùng nhau khi so sánh phiên bản.
- Quan sát metrics, logs, traces và alert cần dữ liệu thật từ stack; nên bổ sung alert cho error rate, p95, chi phí và chất lượng eval.
