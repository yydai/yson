import decoder


test_1 = '{"hello": "world", "true": true, "false": false}'
test_2 = '["234", 123, {"ha": "ha"}, ["en", 32], true, false, null]'


json = decoder.JSONDecoder()
print json.decode(test_1)
print json.decode(test_2)
