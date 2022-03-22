import { check } from 'k6'
import http from 'k6/http'
import crypto from 'k6/crypto'

const num_different_images = parseInt(__ENV.NUM_IMAGES)
// Init stage. Each file only needs to be loaded once for many tests
const image_data_array = []
for (let i=0; i<num_different_images; i++) {
	image_data_array.push(open(__ENV.IMAGE_FILE_PREFIX + i.toString() + '.jpg'))
}

const base_url = __ENV.BASE_URL
	
export default function() {
	const trace_header = getTraceHeader()

	const image_to_use = randomIntBetween(0, num_different_images-1)
	
	const res = http.request('POST', `${base_url}/upload/img-${trace_header.trace_id}.jpg`, image_data_array[image_to_use], {
		headers: {
			'Content-Type': 'multipart/form-data',
			'traceparent': trace_header.header
		},	
		tags: { // Each request is tagged in the metrics with the corresponding trace header
			trace_header: trace_header.header,
		}
	})
	
	// to debug
	// console.log(JSON.stringify(res))
	console.log(">>>>>> i am k6 in azure:" + trace_header.header)
	console.log(">>>>>> response: " + res.status)

	check(res, {
		'status is 200': (res) => res.status === 200,
	})
}

function randomIntBetween(min, max) { // min and max included
	return Math.floor(Math.random() * (max - min + 1) + min);
}

function getTraceHeader() {

	const trace_id = crypto.hexEncode(crypto.randomBytes(16))
	const parent_id = crypto.hexEncode(crypto.randomBytes(8))

	return {
        trace_id: trace_id,
        header: `00-${trace_id}-${parent_id}-01`
    };
}

// Copied from https://stackoverflow.com/a/55200387
const byteToHex = [];

for (let n = 0; n <= 0xff; ++n)
{
	const hexOctet = n.toString(16).padStart(2, '0');
	byteToHex.push(hexOctet);
}

function hex(arrayBuffer)
{
	const buff = new Uint8Array(arrayBuffer);
	const hexOctets = []; // new Array(buff.length) is even faster (preallocates necessary array size), then use hexOctets[i] instead of .push()

	for (let i = 0; i < buff.length; ++i)
		hexOctets.push(byteToHex[buff[i]]);

	return hexOctets.join('');
}
