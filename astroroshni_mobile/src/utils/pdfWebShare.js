/** Create a real PDF for browser sharing; browser print produces no shareable file. */
export async function renderShareablePdfOnWeb(html) {
  const [{ jsPDF }, { default: html2canvas }] = await Promise.all([import('jspdf'), import('html2canvas')]);
  // Isolate the full HTML document from PWA styles and preserve its stylesheet.
  const frame = document.createElement('iframe');
  frame.setAttribute('aria-hidden', 'true');
  frame.style.cssText = 'position:fixed;left:-10000px;top:0;width:820px;height:1100px;border:0;background:white;pointer-events:none;';
  document.body.appendChild(frame);
  try {
    const page = frame.contentDocument;
    if (!page) throw new Error('Could not create the PDF document');
    page.open(); page.write(html); page.close();
    if (page.fonts?.ready) await page.fonts.ready;
    await Promise.all(Array.from(page.images).map(img => img.complete ? Promise.resolve() : new Promise(resolve => {
      img.onload = resolve; img.onerror = resolve;
    })));
    const height = Math.max(page.body.scrollHeight, page.documentElement.scrollHeight);
    frame.style.height = `${height}px`;
    const canvas = await html2canvas(page.body, {useCORS:true, backgroundColor:'#ffffff', scale:1.5,
      windowWidth:820, windowHeight:height, scrollX:0, scrollY:0});
    if (!canvas.width || !canvas.height) throw new Error('The PDF document could not be rendered');
    const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
    let hasContent = false;
    for (let i=0; i<pixels.length; i+=4) {
      if (pixels[i+3] && (pixels[i]<245 || pixels[i+1]<245 || pixels[i+2]<245)) {hasContent=true; break;}
    }
    if (!hasContent) throw new Error('The PDF rendered blank');
    const doc = new jsPDF({unit:'pt', format:'a4', compress:true});
    const margin=30, width=doc.internal.pageSize.getWidth()-margin*2;
    const pageHeight=doc.internal.pageSize.getHeight()-margin*2;
    const sliceHeight=Math.max(1, Math.floor(pageHeight*canvas.width/width));
    for (let y=0; y<canvas.height; y+=sliceHeight) {
      const slice=document.createElement('canvas');
      slice.width=canvas.width; slice.height=Math.min(sliceHeight,canvas.height-y);
      slice.getContext('2d').drawImage(canvas,0,y,canvas.width,slice.height,0,0,canvas.width,slice.height);
      if (y>0) doc.addPage();
      doc.addImage(slice.toDataURL('image/png'),'PNG',margin,margin,width,slice.height*width/canvas.width, undefined, 'FAST');
    }
    return doc.output('blob');
  } finally {frame.remove();}
}

export async function sharePdfBlobOnWeb(blob, options = {}) {
  const filename = `AstroRoshni-Prediction-${Date.now()}.pdf`;
  const file = new File([blob], filename, { type: 'application/pdf' });
  if (typeof navigator.share === 'function'
      && typeof navigator.canShare === 'function'
      && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: options.dialogTitle || 'AstroRoshni Prediction' });
      return;
    } catch (error) {
      if (error?.name === 'AbortError') return;
      // Async PDF rendering can consume the browser's user activation.
      // Provide the file as a download when opening the share sheet is denied.
      if (error?.name !== 'NotAllowedError') throw error;
    }
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  try {
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
}
