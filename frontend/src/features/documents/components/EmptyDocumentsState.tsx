export function EmptyDocumentsState() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50 bg-background">
      <h3 className="text-2xl font-semibold tracking-tight">No documents found</h3>
      <p className="text-sm text-muted-foreground mt-2 max-w-md">
        This workspace doesn't have any documents yet. Upload a document to start extracting insights and chatting with your data.
      </p>
    </div>
  );
}
