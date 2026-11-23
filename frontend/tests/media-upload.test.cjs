const {test} = require('node:test');
const assert = require('node:assert/strict');
const {blobBase64, RecordingUploader} = require('../media-upload.js');

test('camera codec commas do not corrupt binary data', async () => {
  const raw = Buffer.from([0, 255, 26, 69, 223, 163, 44, 128]);
  const blob = new Blob([raw], {type:'video/webm;codecs=vp8,opus'});
  assert.deepEqual(Buffer.from(await blobBase64(blob), 'base64'), raw);
});
test('large blobs are split and reconstructed in order', async () => {
  const raw = Buffer.alloc(3 * 1024 * 1024 + 43, 217);
  const packets=[];
  const uploader=new RecordingUploader(async packet=>packets.push(packet));
  await uploader.add(new Blob([raw]));
  assert.equal(packets.length,7);
  assert.deepEqual(packets.map(p=>p.sequence),[0,1,2,3,4,5,6]);
  assert.deepEqual(Buffer.concat(packets.map(p=>Buffer.from(p.content,'base64'))),raw);
});
test('failed upload retains bytes and sequence for recovery', async () => {
  let offline=true;const accepted=[];
  const uploader=new RecordingUploader(async p=>{if(offline)throw Error('Offline');accepted.push(p)});
  await assert.rejects(uploader.add(new Blob(['first'])));
  assert.equal(uploader.pending.length,1);
  assert.equal(uploader.sequence,0);
  offline=false;
  await uploader.add(new Blob(['second']));
  assert.deepEqual(accepted.map(p=>p.sequence),[0,1]);
  assert.equal(Buffer.concat(accepted.map(p=>Buffer.from(p.content,'base64'))).toString(),'firstsecond');
  assert.equal(uploader.error,null);
});
test('simultaneous chunks share one ordered drain', async () => {
  const accepted=[];
  const uploader=new RecordingUploader(async p=>{await new Promise(r=>setTimeout(r,2));accepted.push(p)});
  await Promise.all([uploader.add(new Blob(['a'])),uploader.add(new Blob(['b']))]);
  assert.deepEqual(accepted.map(p=>p.sequence),[0,1]);
});
