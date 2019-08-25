from marshmallow import Schema, fields, validate


class BlankInteger(fields.Integer):
    def _deserialize(self, value, attr, obj, **kwargs):
        if value == '':
            return None
        return super()._deserialize(value, attr, obj, **kwargs)


class NullableRange(validate.Range):
    def __call__(self, value):
        if value is None:
            return

        super().__call__(value)


RADIO_MODES = ['FM', 'DMR', 'AM', 'DV']
TX_POWER = ['high', 'low']
ADMIT_CRITERIA = ['free', 'tone', 'color']
SKIP_MODES = ['p', 's', '']


class Channel(Schema):
    name = fields.Str(required=True)
    frequency = fields.Float(required=True)
    offset = fields.Float()
    mode = fields.Str(required=True,
                      validate=validate.OneOf(RADIO_MODES))
    comment = fields.Str()
    duplex = fields.Str()
    rtonefreq = fields.Float()
    ctonefreq = fields.Float()
    dtcscode = fields.Integer()
    dtcspolarity = fields.Str()
    skip = fields.Str(validate=validate.OneOf(SKIP_MODES))
    tone = fields.Str()
    tune_step = fields.Float()
    tx_timeout = BlankInteger()
    tx_power = fields.Str(validate=validate.OneOf(TX_POWER))
    rxonly = fields.Boolean()
    admit = fields.Str(validate=validate.OneOf(ADMIT_CRITERIA))
    scan_list = BlankInteger()
    squelch_level = BlankInteger()
    bandwidth = fields.Float()

    # specific to DMR
    color = BlankInteger(validate=NullableRange(min=0, max=15))
    slot = BlankInteger(validate=NullableRange(min=1, max=2))
    scan_list = BlankInteger()
    rx_group = BlankInteger()
    tx_contact = BlankInteger()
