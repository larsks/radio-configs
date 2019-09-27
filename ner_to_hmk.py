#!/usr/bin/python3

import csv
import click
import collections
import itertools
import logging
import sys

import bandplan
import schema

LOG = logging.getLogger(__name__)

HMK_HEADER = '''KENWOOD MCP FOR AMATEUR MOBILE TRANSCEIVER
[Export Software]=MCP-2A Version 3.22
[Export File Version]=1
[Type]=K
[Language]=English

// Coments
!! Comments=

// Memory Channels
!!Ch,Rx Freq.,Rx Step,Offset,T/CT/DCS,TO Freq.,CT Freq.,DCS Code,Shift/Split,Rev.,L.Out,Mode,Tx Freq.,Tx Step,M.Name
'''

FORMATS = {
    'channel': '{:04d}',
    'rx_freq': '{:012.6f}',
    'tx_freq': '{:012.6f}',
    'rx_step': '{:05.1f}',
    'tx_step': '{:05.1f}',
    'offset': '{:09.6f}',
}


def remove_empty_fields(fields):
    return {
        field: value
        for field, value in fields.items()
        if value is not None
        and (not isinstance(value, str) or value.strip() != '')
    }


def format_fields(channel):
    for k, v in channel.items():
        if k in FORMATS:
            channel[k] = FORMATS[k].format(v)


def show_validation_errors(stage, callsign, errors):
    for fname, messages in errors.items():
        for msg in messages:
            LOG.error('%s %s: %s: %s', stage, callsign, fname, msg)

@click.command()
@click.option('-v', '--verbose', count=True)
@click.option('-i', '--input', type=click.File('r'), default=sys.stdin)
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
@click.option('-b', '--band', multiple=True)
@click.option('-s', '--state', multiple=True)
@click.option('-S', '--start-index', default=0)
@click.option('-m', '--mode', multiple=True, default=['nfm', 'fm'])
@click.option('--offline', is_flag=True)
def main(verbose, input, output, band, state, start_index, mode, offline):

    try:
        loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    except IndexError:
        loglevel = 'DEBUG'

    logging.basicConfig(level=loglevel)

    output.write(HMK_HEADER)

    channel = itertools.count(start_index)
    mode = set([m.lower() for m in mode])

    with input, output:
        repeaters = csv.DictReader(
            input,
            fieldnames=list(schema.NER_Channel.declared_fields.keys()))
        hmk = csv.DictWriter(
            output,
            list(schema.Kenwood_Channel.declared_fields.keys()))

        for row in repeaters:
            callsign = row['callsign']
            ner, errors = schema.NER_Channel.load(remove_empty_fields(row))

            if (errors):
                show_validation_errors('reading', callsign, errors)
                continue

            if ner.get('status') == 'OFF' and not offline:
                continue

            if state:
                state = [s.lower() for s in state]
                if ner['state'].lower() not in state:
                    LOG.info('skipping %s: state %s not in %s',
                             ner['callsign'], ner['state'].lower(), state)
                    continue

            freq_band = bandplan.freq_to_band(ner['rx_freq'])
            if band:
                band = [b.lower() for b in band]
                if freq_band.name.lower() not in band:
                    LOG.info('skipping %s: frequency %0.3f not in %s',
                             ner['callsign'], ner['rx_freq'], band)
                    continue

            for i, ch_mode in enumerate(ner['mode']):
                try:
                    tone_freq = ner['tx_tone'][i]
                except KeyError:
                    tone_freq = None

                if mode and ch_mode.lower() not in mode:
                    LOG.info('skipping %s: mode %s not in %s',
                             ner['callsign'],
                             ch_mode, mode)
                    continue

                ct_freq = ner.get('rx_tone')
                if tone_freq and ct_freq == tone_freq:
                    tone_mode = 'CT'
                elif tone_freq:
                    tone_mode = 'T'
                else:
                    tone_mode = 'Off'

                if ner['offset'] == '-':
                    offset_dir = '-'
                elif ner['offset'] == '+':
                    offset_dir = '+'
                else:
                    offset_dir = ' '

                ken, errors = schema.Kenwood_Channel.load(dict(
                    rx_freq=ner['rx_freq'],
                    tx_freq=ner['rx_freq'],
                    rx_step=freq_band.step,
                    tx_step=freq_band.step,
                    offset=freq_band.offset,
                    tone_mode=tone_mode,
                    tone_freq=tone_freq,
                    ct_freq=ct_freq,
                    dcs_code=0,
                    shift=offset_dir,
                    mode=ch_mode,
                    name=ner['callsign'][:6]
                ))

                if (errors):
                    show_validation_errors('converting', callsign, errors)
                    continue

                row_out, errors = schema.Kenwood_Channel.dump(ken)
                if (errors):
                    show_validation_errors('writing', callsign, errors)
                    continue

                row_out['channel'] = next(channel)
                format_fields(row_out)
                hmk.writerow(row_out)


if __name__ == '__main__':
    main()
