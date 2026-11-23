/* Binary conversion never parses a data URL: codec names can contain commas. */
async function blobBase64(blob) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = '';
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
  }
  return btoa(binary);
}

class RecordingUploader {
  constructor(send) {
    this.send = send;
    this.pending = [];
    this.sequence = 0;
    this.running = null;
    this.error = null;
  }
  add(blob) {
    // Browser suspension can produce blobs larger than the requested timeslice.
    for (let i = 0; i < blob.size; i += 512 * 1024) {
      this.pending.push(blob.slice(i, i + 512 * 1024));
    }
    return this.flush();
  }
  flush() {
    if (this.running) return this.running;
    this.running = this.drain().finally(() => { this.running = null; });
    return this.running;
  }
  async drain() {
    try {
      while (this.pending.length) {
        const content = await blobBase64(this.pending[0]);
        let failure;
        for (let attempt = 0; attempt < 3; attempt++) {
          try { await this.send({sequence: this.sequence, content}); failure = null; break; }
          catch (error) { failure = error; }
        }
        if (failure) throw failure;
        this.pending.shift();
        this.sequence++;
      }
      this.error = null;
    } catch (error) {
      this.error = error.message;
      throw error; // Keep the failed chunk and sequence for the next retry.
    }
  }
}
if (typeof module !== 'undefined') module.exports = {blobBase64, RecordingUploader};
