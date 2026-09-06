# Repository Instructions & Guardrails

## 1. CRITICAL: Dev Server Safety (TUYỆT ĐỐI KHÔNG CHẠY `npm run build` KHI ĐANG DEV)
- **KHÔNG ĐƯỢC CHẠY `npm run build` hoặc `next build` để kiểm tra code trong `apps/web`.**
- **Lý do**: Người dùng đang chạy dev server (`npm run dev`) qua `start.bat`. Khi chạy `next build`, Next.js sẽ ghi đè thư mục `.next` bằng bản build production tĩnh. Điều này làm hỏng bộ nhớ đệm của `next dev` đang chạy và khiến người dùng bị lỗi `500 Internal Server Error` hoặc lỗi mất chunk khi bấm **F5** trên trình duyệt, buộc người dùng phải khởi động lại.
- **Quy chuẩn kiểm tra (Verification)**: Luôn luôn sử dụng `npm run typecheck` (`tsc --noEmit`) trong thư mục `apps/web` để kiểm tra kiểu dữ liệu và cú pháp TypeScript mà KHÔNG động chạm đến thư mục `.next`.

## 2. Quản Lý Khởi Động & Dịch Vụ (Scripts)
- Backend: FastAPI tại `http://localhost:8000` (`apps/api`).
- Frontend: Next.js tại `http://localhost:3000` (`apps/web`).
- `start.bat`: Khởi động nhanh (tự động bỏ qua `pip install` lặp lại thừa thãi). Chạy `start.bat install` nếu cần cài/cập nhật thư viện mới.
- `restart.bat`: Khởi động lại dịch vụ nhanh chóng.
- `stop.bat`: Tắt toàn bộ dịch vụ trên cổng 8000 và 3000.
