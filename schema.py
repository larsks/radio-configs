from marshmallow import Schema, fields, validate, pre_load, missing


class NoneIsMissingSchema(Schema):
    @classmethod
    def get_attribute(cls, attr, obj, default):
        return (
            Schema.get_attribute(cls, attr, obj, default)
            or missing
        )


class BlankFloat(fields.Float):
    def _deserialize(self, value, attr, obj, **kwargs):
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None
        return super()._deserialize(value, attr, obj, **kwargs)


class DelimitedList(fields.Field):
    def __init__(self, delim='/', *args, **kwargs):
        self.delim = delim
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, list):
            raise ValueError('value must be a list')

        return self.delim.join(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return value.strip().split(self.delim)


class OnOffBoolean(fields.Boolean):
    def __init__(self, *args, **kwargs):
        super().__init__(missing='Off', *args, **kwargs)

        self.falsy.add('Off')
        self.truthy.add('On')

    def _serialize(self, value, attr, obj, **kwargs):
        return 'On' if value else 'Off'


class _NER_Channel(Schema):
    rx_freq = fields.Float(required=True)
    offset = fields.Str(validate=validate.OneOf(['-', '+', 'S']))
    state = fields.Str()
    city = fields.Str()
    mode = DelimitedList('/', missing='FM')
    callsign = fields.Str()
    tx_tone = fields.Str()
    rx_tone = fields.Str()
    status = fields.Str()
    county = fields.Str()
    el1 = fields.Str()
    el2 = fields.Str()
    notes = fields.Str()
    date = fields.Str()

    @pre_load
    def clean_tone_fields(self, in_data, **kwargs):
        for fname in ['rx_tone', 'tx_tone']:
            if fname not in in_data:
                continue

            in_data[fname] = in_data[fname].strip('*')

    @pre_load
    def null_empty_fields(self, in_data, **kwargs):
        for k, v in in_data.items():
            if isinstance(v, str) and v.strip() == '':
                in_data[k] = None


class _Kenwood_Channel(Schema):
    rx_freq = fields.Float(required=True)
    rx_step = fields.Float()
    offset = fields.Float()
    tone_mode = fields.Str()
    tone_freq = fields.Float(allow_none=True)
    ct_freq = fields.Float(allow_none=True)
    dcs_code = fields.Int(allow_non=True)
    shift = fields.Str()
    reverse = OnOffBoolean(default=False)
    lockout = OnOffBoolean(default=False)
    mode = fields.Str()
    tx_freq = fields.Float()
    tx_step = fields.Float()
    name = fields.Str(validate=validate.Length(max=6))


NER_Channel = _NER_Channel()
Kenwood_Channel = _Kenwood_Channel()
