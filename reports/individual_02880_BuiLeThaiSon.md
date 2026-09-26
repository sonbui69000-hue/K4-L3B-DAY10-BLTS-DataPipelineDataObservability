# Báo Cáo Cá Nhân — Bui Le Thai Son

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Bui Le Thai Son |
| MSSV | 02880 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | BLTS |
| Vai trò chính | Pipeline owner — thực hiện toàn bộ bài lab cá nhân |
| Repository | K4-L3B-DAY10-BLTS-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Ingestion và raw preservation | src/ingestion/crossref.py | Crossref payload hoặc snapshot | crossref_response.json, crossref_records.json | Hoàn thành |
| Cleaning và benchmark | src/ingestion/cleaning.py, src/evaluation/testset.py | Raw records | Clean dataframe, test_set.json | Hoàn thành |
| Observability | src/observability/quality.py | Clean/corrupted dataframe | GX quality reports, freshness reports | Hoàn thành |
| Pipeline và recovery | src/pipelines/phase1.py, src/pipelines/corruption_flow.py | Raw/clean artifacts | Metrics, repair và comparison report | Hoàn thành |

## 3. Kết quả theo vai trò

| Nhiệm vụ | Artifact | Kết quả xác minh |
|---|---|---|
| Baseline pipeline | data/results/baseline_metrics.json | 10 samples, hit rate 1.0, Token F1 1.0 |
| Corruption flow | data/results/corrupted_metrics.json | Token F1 giảm còn 0.8741, quality gate FAIL |
| Raw snapshot repair | data/results/repaired_metrics.json | Token F1 phục hồi lên 1.0, quality gate PASS |
| Comparison report | data/reports/corruption_report.md | Có bảng Baseline/Corrupted/Repaired |

## 4. Giải thích kỹ thuật

Raw Crossref được parse thành PaperRecord, làm sạch thành dataframe, sau đó embedding bằng all-MiniLM-L6-v2 và index vào ChromaDB. Test set giữ nguyên DOI ground truth để so sánh công bằng giữa ba trạng thái.

Quality Gate dùng Great Expectations 1.x Ephemeral Context với các kiểm tra row count, non-null, unique và summary length. Freshness được đánh giá riêng theo tỷ lệ age_days lớn hơn 180 ngày.

Corruption tạo sáu lỗi: bỏ bản ghi mới nhất, xóa summary, chèn noise, cắt title, lùi ngày và duplicate rows. Repair không sửa trực tiếp dataframe lỗi mà rebuild từ raw snapshot.

## 5. Quyết định kỹ thuật

Chọn repair từ raw snapshot thay vì chỉnh ngược dataframe corrupted. Cách này bảo toàn data lineage, có tính idempotent và chứng minh hệ thống phục hồi từ nguồn đáng tin cậy.

## 6. Lỗi/blocker đã xử lý

Sandbox Linux gặp lỗi mountinfo path is not absolute trong codex-cli. Các thao tác repository được thực hiện bằng command path đã được phê duyệt. Ngoài ra, Great Expectations 1.23.2 yêu cầu import non-null expectation từ module cụ thể thay vì package export trực tiếp; đã điều chỉnh và xác minh quality gate thành công.

## 7. Hiểu biết end-to-end

Crossref tạo raw artifacts làm lineage anchor. Cleaning tạo schema phục vụ embedding. ChromaDB cung cấp retrieval. Evaluation dùng cùng 10 câu hỏi và DOI ground truth cho cả baseline, corrupted và repaired. Quality checks phát hiện lỗi cấu trúc; freshness theo dõi tuổi dữ liệu. Repair thành công khi dataset, quality gate và metrics trở về trạng thái baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| retrieval_hit_rate | 1.0 | 1.0 | 1.0 |
| mean_token_f1 | 1.0 | 0.8741 | 1.0 |
| judge_accuracy | 1.0 | 0.9 | 1.0 |
| mean_judge_score | 5 | 4.4 | 5 |
| Quality checks | PASS | FAIL | PASS |
| Freshness stale ratio | 4.17% | 14.29% | 4.17% |

Corruption làm quality gate thất bại và làm giảm Token F1/Judge Score, dù retrieval hit rate vẫn giữ nguyên. Đây là bằng chứng của silent failure ở answer quality. Repair từ raw snapshot phục hồi dataset 24 dòng và toàn bộ metrics chính.

## 9. Điều học được

1. Raw preservation là nền tảng cho lineage và recovery.
2. Quality gate phải kiểm tra cả schema/content, không chỉ pipeline runtime.
3. Retrieval thành công không đảm bảo câu trả lời cuối cùng vẫn chính xác.

Nếu có thêm thời gian, có thể bổ sung automated tests và dashboard theo dõi quality/freshness theo từng lần chạy.

## 10. Cam kết

- [x] Báo cáo phản ánh đúng phần việc cá nhân.
- [x] Có thể giải thích toàn bộ luồng end-to-end.
- [x] Kết luận dựa trên artifacts và metrics thực tế.
- [x] Không ghi secret, API key hoặc token.
- [x] Tỷ lệ đóng góp cá nhân: 100%.

**Họ và tên:** Bui Le Thai Son  
**Ngày xác nhận:** 2026-09-26
