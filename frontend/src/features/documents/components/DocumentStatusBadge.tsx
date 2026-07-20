import { Badge } from "@/components/ui/badge";
import { DocumentStatus } from "../types";

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  switch (status) {
    case "uploading":
      return <Badge variant="outline" className="text-blue-500 border-blue-500">Uploading</Badge>;
    case "processing":
      return <Badge variant="outline" className="text-yellow-500 border-yellow-500">Processing</Badge>;
    case "ready":
      return <Badge variant="outline" className="text-green-500 border-green-500">Ready</Badge>;
    case "failed":
      return <Badge variant="destructive">Failed</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}
