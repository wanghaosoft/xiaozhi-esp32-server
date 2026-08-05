package xiaozhi.modules.device.dto;

import org.apache.commons.lang3.StringUtils;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "外部设备文本对话请求")
public class ExternalDeviceTextChatDTO {
    @Schema(description = "设备ID，传该值时直接按主键定位设备")
    private String deviceId;

    @Schema(description = "智能体ID，未传 deviceId 时必填，并与 macAddress 组合唯一定位设备")
    private String agentId;

    @Schema(description = "设备 MAC 地址，未传 deviceId 时必填，并与 agentId 组合唯一定位设备")
    private String macAddress;

    @NotBlank(message = "文本内容不能为空")
    @Schema(description = "发送给设备的文本内容")
    private String text;

    @Schema(description = "是否先打断设备当前对话，默认 true")
    private Boolean interrupt = true;

    @AssertTrue(message = "请提供 deviceId，或同时提供 agentId 与 macAddress")
    public boolean isLocatorValid() {
        return StringUtils.isNotBlank(deviceId)
                || (StringUtils.isNotBlank(agentId) && StringUtils.isNotBlank(macAddress));
    }
}