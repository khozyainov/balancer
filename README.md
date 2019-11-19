# balancer

## Запуск
```bash 
docker-compose -f balancer-compose.yaml -f redis-compose.yaml  up --build -d
```

## Тестирование
```bash 
docker-compose -f test-compose.yaml up --build
```

## Список методов
Редирект на один из серверов
`[GET] /?video=URL`  
```javascript

Response
302 - redirect
400 - GET-параметр `video` отсутствует
500 - неожиданная ошибка при выборе сервера
503 - сервера отсутствуют
```

Установка конфигурации весов и серверов балансировки  
`[POST] /configurate`
```javascript
Request
{
    "http://cdn_a.ru": 10,
    "http://cdn_b.com": 20,
    "http://origin.com": 1
}

Response
200 - OK 
400 - невалидный json с параметрами, ошибка при парсинге json-а
500 - ошибка конфигурации
```