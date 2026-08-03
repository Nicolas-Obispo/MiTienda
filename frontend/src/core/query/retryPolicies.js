export function retryExceptNotFound(failureCount, error) {
  if (error?.status === 404) return false;

  return failureCount < 1;
}
