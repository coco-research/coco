import { Navigate } from 'react-router-dom';

export default function JarvisPage() {
  return <Navigate to="/?jarvis=true" replace />;
}
