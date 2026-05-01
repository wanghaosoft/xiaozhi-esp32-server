package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "设备文本对话请求")
public class DeviceTextChatDTO {
    @NotBlank(message = "文本内容不能为空")
    @Schema(description = "发送给设备的文本内容")
    private String text;

    @Schema(description = "是否先打断设备当前对话，默认true")
    private Boolean interrupt = true;
}