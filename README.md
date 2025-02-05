# pdf2htmlEX-Server
用於轉換PDF至HTML檔案的伺服器，提供用以上傳PDF、查詢轉換進度、下載HTML的API。

## APIs
- **POST ```/pdf```**
  
  收取用戶上傳的PDF檔案，生成一個token返回給用戶，並開始轉換檔案。

- **GET ```/task/{token}```**
  
  透過token查詢上傳PDF的轉換進度。

- **GET ```/html/{token}```**
  
  透過token下載轉換完成之對應HTML檔案。

## 依賴項目
- Python > 3.6
- docker

## 安裝
執行```install.bat```

## 使用方法
執行```start_server.bat```

## Credits
此程式使用了*pdf2htmlEX* (https://github.com/pdf2htmlEX/pdf2htmlEX) 發佈之docker image作為PDF檔案轉換工具。