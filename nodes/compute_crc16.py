from pymodbus.framer.rtu import FramerRTU

from gen.messages_pb2 import ComputeCrc16Input, ComputeCrc16Output
from gen.axiom_context import AxiomContext
def compute_crc16(ax: AxiomContext, input: ComputeCrc16Input) -> ComputeCrc16Output:
    """Compute the Modbus RTU CRC16 (initial value 0xFFFF, polynomial 0xA001)
    over arbitrary bytes — typically a frame's device id + function code +
    data, ahead of appending it as the two trailing wire bytes. Optionally
    validates an expected CRC16 in the same call.
    """
    data = input.data
    crc16 = FramerRTU.compute_CRC(bytes(data))
    crc16_bytes = crc16.to_bytes(2, "big")
    matches = (crc16 == input.expected_crc16) if input.validate else False
    return ComputeCrc16Output(crc16=crc16, crc16_bytes=crc16_bytes, matches=matches)
