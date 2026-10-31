import React, { useEffect, useId, useRef, useState } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from 'html5-qrcode';

interface RoomQrScannerProps {
  onScan: (value: string) => void;
}

export const RoomQrScanner: React.FC<RoomQrScannerProps> = ({ onScan }) => {
  const generatedId = useId();
  const scannerId = `room-qr-scanner-${generatedId.replace(/:/g, '')}`;
  const onScanRef = useRef(onScan);
  const deliveredScan = useRef(false);
  const [cameraError, setCameraError] = useState('');

  useEffect(() => {
    onScanRef.current = onScan;
  }, [onScan]);

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      scannerId,
      {
        fps: 10,
        qrbox: { width: 240, height: 240 },
        formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        rememberLastUsedCamera: true,
      },
      false
    );

    try {
      scanner.render(
        (decodedText) => {
          if (deliveredScan.current) return;
          deliveredScan.current = true;
          onScanRef.current(decodedText);
        },
        () => {}
      );
    } catch (error) {
      console.error('Failed to start room QR scanner', error);
      setCameraError('Could not start the camera. Allow camera access and try again.');
    }

    return () => {
      scanner.clear().catch((error) => {
        console.error('Failed to stop room QR scanner', error);
      });
    };
  }, [scannerId]);

  return (
    <div>
      {cameraError && (
        <p role="alert" className="mb-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">
          {cameraError}
        </p>
      )}
      <div id={scannerId} />
    </div>
  );
};
