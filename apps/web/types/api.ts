export interface ApiErrorDetail {
  field?: string;
  msg: string;
  type?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: {
    errors?: ApiErrorDetail[];
    [key: string]: unknown;
  };
}

export interface ApiResponseError {
  error: ApiError;
}
