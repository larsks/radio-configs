import json
import marshmallow
import yaml

import schema

with open('channels.yaml') as fd:
    data = yaml.safe_load(fd)

channel_schema = schema.Channel()
for channel in data['channels']:
    try:
        _channel = channel_schema.load(channel, unknown='EXCLUDE')
    except marshmallow.exceptions.ValidationError as err:
        print(err.messages)
        for field in err.args[0]:
            print(field, '=', channel[field])
        break

    print(json.dumps(_channel, indent=2))
