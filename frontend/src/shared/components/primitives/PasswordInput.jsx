import { forwardRef, useState } from "react";

import Button from "./Button";
import { Input } from "./FormControls";

const PasswordInput = forwardRef(function PasswordInput(
  {
    hideLabel = "Ocultar contraseña",
    showLabel = "Mostrar contraseña",
    ...props
  },
  ref
) {
  const [visible, setVisible] = useState(false);

  return (
    <Input
      {...props}
      ref={ref}
      type={visible ? "text" : "password"}
      trailingAction={
        <Button
          type="button"
          onClick={() => setVisible((current) => !current)}
          variant="ghost"
          iconOnly
          aria-label={visible ? hideLabel : showLabel}
          aria-pressed={visible}
        >
          <span aria-hidden="true">{visible ? "🙉" : "🙈"}</span>
        </Button>
      }
    />
  );
});

export default PasswordInput;
