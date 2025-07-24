# Trợ lý Xếp lịch Thông minh (DSS Schedule Project)

Dự án này sử dụng Thuật toán Di truyền để tự động tạo ra lịch trình công việc tối ưu.

## Hướng dẫn Cài đặt và Chạy

### 1\. Tạo và kích hoạt môi trường ảo

  * **Tạo môi trường ảo:**

    ```bash
    python -m venv venv
    ```

  * **Kích hoạt môi trường ảo:**

      * Trên Windows:
        ```bash
        .\venv\Scripts\activate
        ```
      * Trên macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

### 2\. Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

### 3\. Chạy ứng dụng

  * **Chạy trên giao diện web (Streamlit):**

    ```bash
    streamlit run app.py
    ```