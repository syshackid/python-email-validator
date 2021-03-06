from unittest import mock
import dns.resolver
import pytest
from email_validator import EmailSyntaxError, EmailUndeliverableError, \
                            validate_email, validate_email_deliverability, \
                            caching_resolver, ValidatedEmail
# Let's test main but rename it to be clear
from email_validator import main as validator_main


@pytest.mark.parametrize(
    'email_input,output',
    [
        (
            'Abc@example.com',
            ValidatedEmail(
                local_part='Abc',
                ascii_local_part='Abc',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='Abc@example.com',
                ascii_email='Abc@example.com',
            ),
        ),
        (
            'Abc.123@example.com',
            ValidatedEmail(
                local_part='Abc.123',
                ascii_local_part='Abc.123',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='Abc.123@example.com',
                ascii_email='Abc.123@example.com',
            ),
        ),
        (
            'user+mailbox/department=shipping@example.com',
            ValidatedEmail(
                local_part='user+mailbox/department=shipping',
                ascii_local_part='user+mailbox/department=shipping',
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email='user+mailbox/department=shipping@example.com',
                ascii_email='user+mailbox/department=shipping@example.com',
            ),
        ),
        (
            "!#$%&'*+-/=?^_`.{|}~@example.com",
            ValidatedEmail(
                local_part="!#$%&'*+-/=?^_`.{|}~",
                ascii_local_part="!#$%&'*+-/=?^_`.{|}~",
                smtputf8=False,
                ascii_domain='example.com',
                domain='example.com',
                email="!#$%&'*+-/=?^_`.{|}~@example.com",
                ascii_email="!#$%&'*+-/=?^_`.{|}~@example.com",
            ),
        ),
        (
            '?????????@??????.??????',
            ValidatedEmail(
                local_part='?????????',
                smtputf8=True,
                ascii_domain='xn--5nqv22n.xn--lhr59c',
                domain='??????.??????',
                email='?????????@??????.??????',
            ),
        ),
        (
            '?????????@????????????.???????????????',
            ValidatedEmail(
                local_part='?????????',
                smtputf8=True,
                ascii_domain='xn--l2bl7a9d.xn--o1b8dj2ki',
                domain='????????????.???????????????',
                email='?????????@????????????.???????????????',
            ),
        ),
        (
            '????????@??????????????.??????',
            ValidatedEmail(
                local_part='????????',
                smtputf8=True,
                ascii_domain='xn--80ajglhfv.xn--j1aef',
                domain='??????????????.??????',
                email='????????@??????????????.??????',
            ),
        ),
        (
            '????????@??????????????.??????',
            ValidatedEmail(
                local_part='????????',
                smtputf8=True,
                ascii_domain='xn--mxahbxey0c.xn--xxaf0a',
                domain='??????????????.??????',
                email='????????@??????????????.??????',
            ),
        ),
        (
            '?????????@????????????.tw',
            ValidatedEmail(
                local_part='?????????',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='????????????.tw',
                email='?????????@????????????.tw',
            ),
        ),
        (
            'jeff@????????????.tw',
            ValidatedEmail(
                local_part='jeff',
                ascii_local_part='jeff',
                smtputf8=False,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='????????????.tw',
                email='jeff@????????????.tw',
                ascii_email='jeff@xn--fiqq24b10vi0d.tw',
            ),
        ),
        (
            '?????????@????????????.??????',
            ValidatedEmail(
                local_part='?????????',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.xn--kpry57d',
                domain='????????????.??????',
                email='?????????@????????????.??????',
            ),
        ),
        (
            'jeff???@????????????.tw',
            ValidatedEmail(
                local_part='jeff???',
                smtputf8=True,
                ascii_domain='xn--fiqq24b10vi0d.tw',
                domain='????????????.tw',
                email='jeff???@????????????.tw',
            ),
        ),
        (
            '??o????@example.com',
            ValidatedEmail(
                local_part='??o????',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='??o????@example.com',
            ),
        ),
        (
            '??????@example.com',
            ValidatedEmail(
                local_part='??????',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='??????@example.com',
            ),
        ),
        (
            '??????????????????@example.com',
            ValidatedEmail(
                local_part='??????????????????',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='??????????????????@example.com',
            ),
        ),
        (
            '??????????????????????????-??-??????????????????????.????@example.com',
            ValidatedEmail(
                local_part='??????????????????????????-??-??????????????????????.????',
                smtputf8=True,
                ascii_domain='example.com',
                domain='example.com',
                email='??????????????????????????-??-??????????????????????.????@example.com',
            ),
        ),
        (
            '??????????????????.??????????????????@domain.with.idn.tld',
            ValidatedEmail(
                local_part='??????????????????.??????????????????',
                smtputf8=True,
                ascii_domain='domain.with.idn.tld',
                domain='domain.with.idn.tld',
                email='??????????????????.??????????????????@domain.with.idn.tld',
            ),
        ),
        (
            '??????????????@????????.gr',
            ValidatedEmail(
                local_part='??????????????',
                smtputf8=True,
                ascii_domain='xn--qxaa9ba.gr',
                domain='????????.gr',
                email='??????????????@????????.gr',
            ),
        ),
    ],
)
def test_email_valid(email_input, output):
    # print(f'({email_input!r}, {validate_email(email_input, check_deliverability=False)!r}),')
    assert validate_email(email_input, check_deliverability=False) == output


@pytest.mark.parametrize(
    'email_input,error_msg',
    [
        ('my@.leadingdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@??????leadingfwdot.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@..twodots.com', 'An email address cannot have a period immediately after the @-sign.'),
        ('my@twodots..com', 'An email address cannot have two periods in a row.'),
        ('my@baddash.-.com',
         'The domain name baddash.-.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@baddash.-a.com',
         'The domain name baddash.-a.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@baddash.b-.com',
         'The domain name baddash.b-.com contains invalid characters (Label must not start or end with a hyphen).'),
        ('my@example.com\n',
         'The domain name example.com\n contains invalid characters (Codepoint U+000A at position 4 of '
         '\'com\\n\' not allowed).'),
        ('my@example\n.com',
         'The domain name example\n.com contains invalid characters (Codepoint U+000A at position 8 of '
         '\'example\\n\' not allowed).'),
        ('.leadingdot@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('..twodots@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('twodots..here@domain.com', 'The email address contains invalid characters before the @-sign: ..'),
        ('me@???wouldbeinvalid.com',
         "The domain name ???wouldbeinvalid.com contains invalid characters (Codepoint U+2488 not allowed "
         "at position 1 in '???wouldbeinvalid.com')."),
        ('@example.com', 'There must be something before the @-sign.'),
        ('\nmy@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
        ('m\ny@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
        ('my\n@example.com', 'The email address contains invalid characters before the @-sign: \n.'),
        ('11111111112222222222333333333344444444445555555555666666666677777@example.com', 'The email address is too long before the @-sign (1 character too many).'),
        ('111111111122222222223333333333444444444455555555556666666666777777@example.com', 'The email address is too long before the @-sign (2 characters too many).'),
        ('me@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444444444455555555556.com', 'The email address is too long after the @-sign.'),
        ('my.long.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333333344444.info', 'The email address is too long (2 characters too many).'),
        ('my.long.address@??111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.11111111112222222222333333.info', 'The email address is too long (when converted to IDNA ASCII).'),
        ('my.long.address@??111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
        ('my.??ong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.111111111122222222223333333333444.info', 'The email address is too long (when encoded in bytes).'),
        ('my.??ong.address@1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444444444555555555.6666666666777777777788888888889999999999000000000.1111111111222222222233333333334444.info', 'The email address is too long (at least 1 character too many).'),
    ],
)
def test_email_invalid(email_input, error_msg):
    with pytest.raises(EmailSyntaxError) as exc_info:
        validate_email(email_input)
    # print(f'({email_input!r}, {str(exc_info.value)!r}),')
    assert str(exc_info.value) == error_msg


def test_dict_accessor():
    input_email = "testaddr@example.com"
    valid_email = validate_email(input_email, check_deliverability=False)
    assert isinstance(valid_email.as_dict(), dict)
    assert valid_email.as_dict()["original_email"] == input_email


def test_deliverability_no_records():
    assert validate_email_deliverability('example.com', 'example.com') == {'mx': [(0, '')], 'mx-fallback': None}


def test_deliverability_found():
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert response.keys() == {'mx', 'mx-fallback'}
    assert response['mx-fallback'] is None
    assert len(response['mx']) > 1
    assert len(response['mx'][0]) == 2
    assert isinstance(response['mx'][0][0], int)
    assert response['mx'][0][1].endswith('.com')


def test_deliverability_fails():
    domain = 'xkxufoekjvjfjeodlfmdfjcu.com'
    with pytest.raises(EmailUndeliverableError, match='The domain name {} does not exist'.format(domain)):
        validate_email_deliverability(domain, domain)


def test_deliverability_dns_timeout():
    validate_email_deliverability.TEST_CHECK_TIMEOUT = True
    response = validate_email_deliverability('gmail.com', 'gmail.com')
    assert "mx" not in response
    assert response.get("unknown-deliverability") == "timeout"
    validate_email('test@gmail.com')
    del validate_email_deliverability.TEST_CHECK_TIMEOUT


def test_main_single_good_input(monkeypatch, capsys):
    import json
    test_email = "test@example.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    output = json.loads(str(stdout))
    assert isinstance(output, dict)
    assert validate_email(test_email).original_email == output["original_email"]


def test_main_single_bad_input(monkeypatch, capsys):
    bad_email = 'test@..com'
    monkeypatch.setattr('sys.argv', ['email_validator', bad_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    assert stdout == 'An email address cannot have a period immediately after the @-sign.\n'


def test_main_multi_input(monkeypatch, capsys):
    import io
    test_cases = ["test@example.com", "test2@example.com", "test@.com", "test3@.com"]
    test_input = io.StringIO("\n".join(test_cases))
    monkeypatch.setattr('sys.stdin', test_input)
    monkeypatch.setattr('sys.argv', ['email_validator'])
    validator_main()
    stdout, _ = capsys.readouterr()
    assert test_cases[0] not in stdout
    assert test_cases[1] not in stdout
    assert test_cases[2] in stdout
    assert test_cases[3] in stdout


def test_main_input_shim(monkeypatch, capsys):
    import json
    monkeypatch.setattr('sys.version_info', (2, 7))
    test_email = b"test@example.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()
    output = json.loads(str(stdout))
    assert isinstance(output, dict)
    assert validate_email(test_email).original_email == output["original_email"]


def test_main_output_shim(monkeypatch, capsys):
    monkeypatch.setattr('sys.version_info', (2, 7))
    test_email = b"test@.com"
    monkeypatch.setattr('sys.argv', ['email_validator', test_email])
    validator_main()
    stdout, _ = capsys.readouterr()

    # This looks bad but it has to do with the way python 2.7 prints vs py3
    # The \n is part of the print statement, not part of the string, which is what the b'...' is
    # Since we're mocking py 2.7 here instead of actually using 2.7, this was the closest I could get
    assert stdout == "b'An email address cannot have a period immediately after the @-sign.'\n"


@mock.patch("dns.resolver.LRUCache.put")
def test_validate_email__with_caching_resolver(mocked_put):
    dns_resolver = caching_resolver()
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_put.called

    with mock.patch("dns.resolver.LRUCache.get") as mocked_get:
        validate_email("test@gmail.com", dns_resolver=dns_resolver)
        assert mocked_get.called


@mock.patch("dns.resolver.LRUCache.put")
def test_validate_email__with_configured_resolver(mocked_put):
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.lifetime = 10
    dns_resolver.cache = dns.resolver.LRUCache(max_size=1000)
    validate_email("test@gmail.com", dns_resolver=dns_resolver)
    assert mocked_put.called

    with mock.patch("dns.resolver.LRUCache.get") as mocked_get:
        validate_email("test@gmail.com", dns_resolver=dns_resolver)
        assert mocked_get.called
