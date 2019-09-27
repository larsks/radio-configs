#!/usr/bin/python3

import csv
import click
import collections
import itertools
import sys

import bandplan
import schema


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


def remove_empty_fields(fields):
    return {
        field: value
        for field, value in fields.items()
        if value is not None
        and (not isinstance(value, str) or value.strip() != '')
    }


@click.command()
@click.option('-i', '--input', type=click.File('r'), default=sys.stdin)
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
@click.option('-b', '--band', multiple=True)
@click.option('-s', '--state', multiple=True)
@click.option('-S', '--start-index', default=0)
@click.option('-m', '--mode', default='fm')
def main(input, output, band, state, start_index, mode):
    output.write(HMK_HEADER)

    channel = itertools.count(start_index)
    with input, output:
        repeaters = csv.DictReader(
            input,
            fieldnames=list(schema.NER_Channel.declared_fields.keys()))
        hmk = csv.DictWriter(
            output,
            fieldnames=['channel'] +
            list(schema.Kenwood_Channel.declared_fields.keys()))

        for row in repeaters:
            row = remove_empty_fields(row)
            ner, errors = schema.NER_Channel.load(row)

            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        print('reading {callsign}: {fname}: {msg}'.format(
                            callsign=row['callsign'],
                            fname=fname,
                            msg=msg),
                              file=sys.stderr)
                continue

            if state:
                state = [s.lower() for s in state]
                if ner['state'].lower() not in state:
                    continue

            freq_band = bandplan.freq_to_band(ner['rx_freq'])
            if band:
                band = [b.lower() for b in band]
                if freq_band.name.lower() not in band:
                    continue

            if mode:
                modes = [m.lower() for m in ner['mode']]
                if mode not in modes:
                    continue

            tone_mode = 'T' if ner.get('tx_tone') else 'Off'
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
                tone_freq=ner.get('tx_tone'),
                ct_freq=ner.get('rx_tone'),
                dcs_code=0,
                shift=offset_dir,
                mode='FM',
                name=ner['callsign'][:6]
            ))

            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        print('converting {callsign}: {fname}: {msg}'.format(
                            callsign=row['callsign'],
                            fname=fname,
                            msg=msg),
                              file=sys.stderr)
                continue

            row_out, errors = schema.Kenwood_Channel.dump(ken)
            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        print('writing {callsign}: {fname}: {msg}'.format(
                            callsign=row['callsign'],
                            fname=fname,
                            msg=msg),
                              file=sys.stderr)
                continue

            row_out['channel'] = next(channel)
            hmk.writerow(row_out)


if __name__ == '__main__':
    main()
