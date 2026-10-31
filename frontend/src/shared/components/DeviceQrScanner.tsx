import React, {
  forwardRef,
  useEffect,
  useId,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

export interface DeviceQrScannerHandle {
  startScanning: () => Promise<void>;
  stopScanning: () => Promise<void>;
}

interface DeviceQrScannerProps {
  onScan: (value: string) => void;
}

export const DeviceQrScanner = forwardRef<DeviceQrScannerHandle, DeviceQrScannerProps>(
  ({ onScan }, ref) => {
    const scannerId = `device-qr-scanner-${useId().replace(/:/g, '')}`;
    const scannerRef = useRef<Html5Qrcode | null>(null);
    const onScanRef = useRef(onScan);
    const startingRef = useRef(false);
    const cancelStartRef = useRef(false);
    const [cameraStatus, setCameraStatus] = useState(
      'Camera is off. Choose “Scan device QR” to start it.'
    );
    const [cameraError, setCameraError] = useState('');

    useEffect(() => {
      onScanRef.current = onScan;
    }, [onScan]);

    useEffect(() => {
      const scanner = new Html5Qrcode(scannerId, {
        formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        verbose: false,
      });
      scannerRef.current = scanner;

      return () => {
        if (scannerRef.current === scanner) scannerRef.current = null;
        const clearScanner = () => {
          try {
            scanner.clear();
          } catch (error) {
            console.error('Failed to clear device QR scanner', error);
          }
        };

        if (scanner.isScanning) {
          void scanner.stop().then(clearScanner).catch((error) => {
            console.error('Failed to stop device QR camera during cleanup', error);
          });
        } else {
          clearScanner();
        }
      };
    }, [scannerId]);

    const stopScanning = async () => {
      const scanner = scannerRef.current;
      if (!scanner) return;
      if (startingRef.current) {
        cancelStartRef.current = true;
        setCameraStatus('Stopping camera…');
        return;
      }
      if (!scanner.isScanning) return;
      try {
        await scanner.stop();
        setCameraStatus('Camera stopped.');
      } catch (error) {
        console.error('Failed to stop device QR camera', error);
        setCameraError('The camera could not be stopped. Close this panel to release it.');
      }
    };

    const startScanning = async () => {
      const scanner = scannerRef.current;
      if (!scanner || scanner.isScanning || startingRef.current) return;

      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        setCameraError(
          'Camera access requires HTTPS (or localhost). Open the deployed app using its secure HTTPS address.'
        );
        return;
      }

      setCameraError('');
      setCameraStatus('Requesting camera permission…');
      cancelStartRef.current = false;
      startingRef.current = true;
      try {
        await scanner.start(
          { facingMode: { ideal: 'environment' } },
          { fps: 10, qrbox: { width: 240, height: 240 } },
          (decodedText) => {
            onScanRef.current(decodedText);
            void stopScanning();
          },
          () => {}
        );
        if (cancelStartRef.current || scannerRef.current !== scanner) {
          await scanner.stop();
          setCameraStatus('Camera stopped.');
          return;
        }
        setCameraStatus('Camera is on. Point it at the QR sticker attached to the device.');
      } catch (error) {
        console.error('Failed to start device QR camera', error);
        const name = error instanceof Error ? error.name : '';
        if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
          setCameraError('Camera permission was denied. Allow camera access for this site, then try again.');
        } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
          setCameraError('No camera was found on this device.');
        } else if (name === 'NotReadableError' || name === 'TrackStartError') {
          setCameraError('The camera is busy in another app or browser tab. Close it and try again.');
        } else {
          setCameraError(
            `Could not open the camera${error instanceof Error ? `: ${error.message}` : '.'}`
          );
        }
        setCameraStatus('');
      } finally {
        startingRef.current = false;
      }
    };

    useImperativeHandle(ref, () => ({ startScanning, stopScanning }));

    return (
      <div>
        <div id={scannerId} className="min-h-12 overflow-hidden rounded-xl" />
        {cameraStatus && (
          <p role="status" className="mt-2 text-xs text-gray-600">
            {cameraStatus}
          </p>
        )}
        {cameraError && (
          <p role="alert" className="mt-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">
            {cameraError}
          </p>
        )}
      </div>
    );
  }
);

DeviceQrScanner.displayName = 'DeviceQrScanner';
