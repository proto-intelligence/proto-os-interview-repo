my_api_project/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── users/
│   │           ├── routes.py
│   │           ├── schemas.py
│   │           └── test_routes.py
│   ├── core/
│   │   ├── config.py
│   │   ├── events.py
│   │   └── logging.py
│   ├── services/
│   │   ├── user_service.py
│   │   └── test_user_service.py
│   ├── integrations/
│   │   ├── stripe/
│   │   │   ├── client.py
│   │   │   └── webhooks.py
│   │   ├── gcp/
│   │   │   ├── pubsub_client.py
│   │   │   └── storage_client.py
│   │   └── ...
│   ├── utils/
│   │   └── sse.py
│   └── main.py
├── settings/
│   ├── base.py
│   ├── dev.py
│   ├── prod.py
│   └── test.py
├── .env
├── pyproject.toml
└── README.md
