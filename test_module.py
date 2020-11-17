from electricity import app

# index page connection test
def test_index():
	response = app.test_client().get("/")
	assert response.status_code == 200

# admin page connection test
def test_admin():
	response = app.test_client().get("/admin")
	assert response.status_code == 200