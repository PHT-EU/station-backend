from cryptography.fernet import Fernet

from station.ctl.config import validators


def test_validate_db_config():
    # invalid password
    db_config = {"admin_user": "admin", "admin_password": "admin"}

    result = validators.validate_db_config(db_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 1
    assert issues[0].display_field == "db.admin_password"

    # invalid username and password
    db_config = {"admin_user": "", "admin_password": "admin"}

    result = validators.validate_db_config(db_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 2

    # valid config
    db_config = {"admin_user": "admin", "admin_password": "valid_password"}

    result = validators.validate_db_config(db_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 0

    # no config given
    db_config = None

    result = validators.validate_db_config(db_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 1


def test_validate_api_config():
    api_config = {"fernet_key": "your_fernet_key"}

    result = validators.validate_api_config(api_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 1
    assert issues[0].display_field == "api.fernet_key"

    api_config = {"fernet_key": "dsa"}

    result = validators.validate_api_config(api_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 1
    assert issues[0].display_field == "api.fernet_key"

    api_config = {"fernet_key": Fernet.generate_key().decode()}
    result = validators.validate_api_config(api_config)
    issues = [
        issue
        for issue in result
        if issue.status != validators.ConfigItemValidationStatus.VALID
    ]
    assert len(issues) == 0


def test_validate_minio_config():
    pass


def test_validate_airflow_config():
    pass


def test_validate_central_config():
    pass
