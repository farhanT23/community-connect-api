from .setup import *

@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    

def test_health():
    response = client.get("/user/health")
    assert response.status_code == 200

def test_create_user():
    # No JSON -> 422 Unprocessable Entity
    response = client.post("/user")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid password format? Assuming you validate
    response = client.post("/user", json={
        "email": "8x9Xt@example.com",
        "password": "1234",
        "name": "test"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Valid input
    response = client.post("/user", json={
        "email": "testt@example.com",
        "password": "p1234!2A8",
        "name": "test"
    })
    assert response.status_code == status.HTTP_201_CREATED

    # Wrong Password
    response = client.post("/user/login", json={
        "email": "testt@example.com",
        "password": "p1234!2A9"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Login
    response = client.post("/user/login", json={
        "email": "testt@example.com",
        "password": "p1234!2A8"
    })
    assert response.status_code == status.HTTP_200_OK


def test_login():
    #Test wrong password
    response = client.post("/user/login", json={
        "email": "testt@example.com",
        "password": "p1234!2A9"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post("/user/login", json={
        "email": "testt@example.com",
        "password": "p1234!2A8"
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"]["email"] == "testt@example.com"
    assert response.json()["token"]["access_token"]